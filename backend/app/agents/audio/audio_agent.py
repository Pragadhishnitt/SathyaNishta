"""Audio agent implementation aligned with contract specs.

This agent exposes contract-aligned tool handlers:
- load_audio_file
- analyze_audio_tone
- detect_deception_markers

`process` expects a task dict of the shape:
{
	"tool": "load_audio_file" | "analyze_audio_tone" | "detect_deception_markers",
	"params": { ... }  # matches the contract for that tool
}
It routes to the corresponding handler and returns the tool's output dict.
"""

import base64
import io
import json
import os
import re
import wave
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger


class AudioAgent(BaseAgent):
	def __init__(self) -> None:
		self.logger = setup_logger(self.__class__.__name__)
		# LLM endpoint (e.g., Portkey or OpenAI-compatible router)
		self.llm_url = os.getenv("LLM_API_URL", "https://api.portkey.ai/v1/chat/completions")
		self.llm_api_key = os.getenv("PORTKEY_API_KEY")
		self.gemini_api_key = os.getenv("GEMINI_API_KEY")
		self.portkey_config = os.getenv("PORTKEY_CONFIG")
		self.llm_model =  self._model_from_portkey_config() or "gemini-2.5-flash"
		self.llm_timeout_sec = int(os.getenv("LLM_TIMEOUT_SEC", "180"))

		# self.supabase_url = os.getenv("SUPABASE_URL")
		# self.supabase_key = os.getenv("SUPABASE_KEY")

		self.tool_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
			"load_audio_file": self.load_audio_file,
			"analyze_audio_tone": self.analyze_audio_tone,
			"detect_deception_markers": self.detect_deception_markers,
		}

	def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
		"""Route the incoming task to the correct audio tool.

		Expected task keys: tool (str), params (dict).
		Raises ValueError for unknown tools or missing params.
		"""

		tool_name = task.get("tool")
		params = task.get("params", {})

		if not tool_name:
			raise ValueError("AudioAgent task missing 'tool'")
		if tool_name not in self.tool_map:
			raise ValueError(f"Unsupported audio tool: {tool_name}")
		if not isinstance(params, dict):
			raise ValueError("AudioAgent task 'params' must be a dict")

		self.logger.debug("Running audio tool", extra={"tool": tool_name, "params": params})
		return self.tool_map[tool_name](params, task)

	# ---------------------------------------------------------------------
	# Tool implementations (contract-compliant shapes)
	# ---------------------------------------------------------------------
	def load_audio_file(self, params: Dict[str, Any], task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""Fetch audio from Supabase Storage or local path and return base64 payload."""

		file_key = params.get("file_key")
		if not file_key:
			raise ValueError("load_audio_file requires 'file_key'")

		start_time_sec = params.get("start_time_sec")
		end_time_sec = params.get("end_time_sec")

		if str(file_key).startswith("synthetic"):
			audio_bytes = self._generate_silent_wav_bytes()
			file_key = "synthetic_silence.wav"
		else:
			audio_bytes = self._read_audio_bytes(file_key)
		audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

		fmt = (Path(file_key).suffix or "").lstrip(".") or "unknown"
		duration_sec = self._estimate_duration_sec(audio_bytes, fmt)

		result: Dict[str, Any] = {
			"file_key": file_key,
			"duration_sec": duration_sec,
			"audio_base64": audio_b64,
			"format": fmt,
			"segment_analyzed": None,
		}

		if start_time_sec is not None or end_time_sec is not None:
			result["segment_analyzed"] = {
				"start_sec": int(start_time_sec or 0),
				"end_sec": int(end_time_sec or duration_sec),
			}

		return result

	def analyze_audio_tone(self, params: Dict[str, Any], task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		return self._call_llm("analyze_audio_tone", params, task)

	def detect_deception_markers(self, params: Dict[str, Any], task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		return self._call_llm("detect_deception_markers", params, task)

	# ------------------------------------------------------------------
	# Internal helper: call LLM and return JSON per contract
	# ------------------------------------------------------------------
	def _call_llm(
		self,
		tool_name: str,
		params: Dict[str, Any],
		task: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Send a structured prompt to the LLM router and parse JSON output.

		The LLM is expected to return a JSON object matching the tool contract.
		Raises RuntimeError on HTTP or parsing issues.
		"""

		if not self.llm_api_key:
			raise RuntimeError("LLM_API_KEY or PORTKEY_API_KEY is not set")

		system_prompt = self._build_system_prompt(tool_name)
		user_content = {
			"tool": tool_name,
			"params": params,
			"metadata": {
				"investigation_id": task.get("investigation_id") if task else None,
				"task_id": task.get("task_id") if task else None,
			},
		}

		body = {
			"model": self.llm_model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": json.dumps(user_content)},
			],
			"temperature": 0.2,
			"response_format": {"type": "json_object"},
		}

		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {self.llm_api_key}",
		}

		portkey_config_header = self._portkey_config_header()
		if portkey_config_header:
			headers["x-portkey-config"] = portkey_config_header

		self.logger.debug("Calling LLM for audio tool", extra={"tool": tool_name, "body": body})

		try:
			response = requests.post(self.llm_url, headers=headers, json=body, timeout=self.llm_timeout_sec)
		except Exception as exc:
			raise RuntimeError(f"LLM request failed: {exc}") from exc

		if not response.ok:
			raise RuntimeError(f"LLM returned {response.status_code}: {response.text}")

		try:
			data = response.json()
			# OpenAI-style responses contain choices[0].message.content
			content = data.get("choices", [{}])[0].get("message", {}).get("content")
			if not content:
				raise ValueError("missing content")
			return json.loads(content)
		except Exception as exc:
			raise RuntimeError("Failed to parse LLM JSON response") from exc

	def _read_audio_bytes(self, file_key: str) -> bytes:
		path = Path(file_key)
		if path.is_file():
			return path.read_bytes()

		if not self.supabase_url or not self.supabase_key:
			raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required to fetch audio")

		if file_key.startswith("http://") or file_key.startswith("https://"):
			url = file_key
		else:
			url = f"{self.supabase_url.rstrip('/')}/storage/v1/object/{file_key.lstrip('/')}"

		headers = {
			"Authorization": f"Bearer {self.supabase_key}",
			"apikey": self.supabase_key,
		}

		response = requests.get(url, headers=headers, timeout=60)
		if not response.ok:
			raise RuntimeError(f"Failed to fetch audio: {response.status_code} {response.text}")
		return response.content

	def _estimate_duration_sec(self, audio_bytes: bytes, fmt: str) -> int:
		if fmt.lower() != "wav":
			return 0

		try:
			with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
				frames = wav_file.getnframes()
				rate = wav_file.getframerate()
				return int(frames / float(rate)) if rate else 0
		except Exception:
			return 0

	def _generate_silent_wav_bytes(self, duration_sec: int = 2, sample_rate: int = 16000) -> bytes:
		"""Generate a short silent WAV for local testing."""

		num_channels = 1
		sample_width = 2
		num_frames = duration_sec * sample_rate
		silent_frame = b"\x00\x00"

		buffer = io.BytesIO()
		with wave.open(buffer, "wb") as wav_file:
			wav_file.setnchannels(num_channels)
			wav_file.setsampwidth(sample_width)
			wav_file.setframerate(sample_rate)
			wav_file.writeframes(silent_frame * num_frames)

		return buffer.getvalue()

	def _build_system_prompt(self, tool_name: str) -> str:
		"""Craft tool-specific instructions with required schema hints."""

		contract_notes = {
			"analyze_audio_tone": "Return segments with start_sec, end_sec, tone_label (confident|nervous|neutral|stressed|hesitant), stress_score (0-1), speaking_pace (slow|normal|fast), pitch_change (stable|rising|falling|erratic), overall_tone, confidence_in_analysis (0-1).",
			"detect_deception_markers": "Return deception_markers list with timestamp_sec, marker_type (hedging_language|topic_avoidance|stress_spike|inconsistency), detail, confidence (0-1), plus hedging_word_count, topic_avoidance_count, overall_deception_likelihood (0-1), explanation.",
		}

		base_rules = [
			"You are the Audio Agent. Output JSON only.",
			"If unsure, return empty lists with low confidence.",
		]

		return " \n".join(base_rules + [contract_notes.get(tool_name, "Follow the contract schema strictly.")])

	def _model_from_portkey_config(self) -> Optional[str]:
		"""Extract model from PORTKEY_CONFIG if present (JSON or key:value text)."""

		if not self.portkey_config:
			return None

		config_text = self.portkey_config.strip()
		try:
			data = json.loads(config_text)
			if isinstance(data, dict):
				model = data.get("model")
				if isinstance(model, str) and model.strip():
					return model.strip()
		except Exception:
			pass

		match = re.search(r"model\s*[:=]\s*[\"']?([\w.-]+)", config_text)
		if match:
			return match.group(1)
		return None

	def _portkey_config_header(self) -> Optional[str]:
		"""Return the x-portkey-config header value, injecting api_key when needed."""

		if not self.portkey_config:
			return None

		config_text = self.portkey_config.strip()
		try:
			data = json.loads(config_text)
			if isinstance(data, dict):
				if data.get("provider") and not data.get("api_key") and self.gemini_api_key:
					data["api_key"] = self.gemini_api_key
				return json.dumps(data)
		except Exception:
			pass

		return self.portkey_config


if __name__ == "__main__":
	try:
		from dotenv import load_dotenv

		repo_root = Path(__file__).resolve().parents[4]
		load_dotenv(repo_root / ".env", override=False)
	except Exception:
		pass

	agent = AudioAgent()

	sample_tasks = [
		{
			"tool": "load_audio_file",
			"params": {
				"file_key": "synthetic",
				"start_time_sec": 0,
				"end_time_sec": 120,
			},
			"investigation_id": "test-audio-001",
			"task_id": "audio-task-001",
		},
		{
			"tool": "analyze_audio_tone",
			"params": {
				"audio_base64": "<set_from_load_audio_file>",
				"context": "revenue discussion",
			},
			"investigation_id": "test-audio-001",
			"task_id": "audio-task-002",
		},
		{
			"tool": "detect_deception_markers",
			"params": {
				"audio_base64": "<set_from_load_audio_file>",
				"transcript": None,
				"focus_topics": ["revenue", "related party transactions"],
			},
			"investigation_id": "test-audio-001",
			"task_id": "audio-task-003",
		},
	]

	for task in sample_tasks:
		if task["tool"] == "load_audio_file":
			result = agent.process(task)
			print("\nTool: load_audio_file")
			print(json.dumps(result, indent=2))
			audio_b64 = result.get("audio_base64")
			for followup in sample_tasks[1:]:
				followup["params"]["audio_base64"] = audio_b64
		else:
			result = agent.process(task)
			print(f"\nTool: {task['tool']}")
			print(json.dumps(result, indent=2))
