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
import wave
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...shared.llm_portkey import chat_complete
from ...core.config import settings


class AudioAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)
        self.llm_timeout_sec = 180

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
    # Internal helper: call LLM via Portkey and return JSON per contract
    # ------------------------------------------------------------------
    def _call_llm(
        self,
        tool_name: str,
        params: Dict[str, Any],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a structured prompt to the LLM via Portkey and parse JSON output.

        The LLM is expected to return a JSON object matching the tool contract.
        Raises RuntimeError on HTTP or parsing issues.
        """

        system_prompt = self._build_system_prompt(tool_name)
        user_content = {
            "tool": tool_name,
            "params": params,
            "metadata": {
                "investigation_id": task.get("investigation_id") if task else None,
                "task_id": task.get("task_id") if task else None,
            },
        }

        self.logger.debug("Calling LLM for audio tool", extra={"tool": tool_name})

        try:
            result = chat_complete(
                user_prompt=json.dumps(user_content),
                system_prompt=system_prompt,
                temperature=0.2,
                metadata={"agent": "audio", "tool": tool_name},
            )
            content = result.get("content")
            if not content:
                raise ValueError("missing content")
            return json.loads(content)
        except Exception as exc:
            raise RuntimeError(f"Audio LLM call failed: {exc}") from exc

    def _read_audio_bytes(self, file_key: str) -> bytes:
        path = Path(file_key)
        if path.is_file():
            return path.read_bytes()

        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_KEY
        if not supabase_url or not supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required to fetch audio")

        if file_key.startswith("http://") or file_key.startswith("https://"):
            url = file_key
        else:
            url = f"{supabase_url.rstrip('/')}/storage/v1/object/{file_key.lstrip('/')}"

        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key,
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
