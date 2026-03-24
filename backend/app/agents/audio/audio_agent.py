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
from typing import Any, Callable, Dict, List, Optional

import requests
from sqlalchemy import text, create_engine
from sqlmodel import Session

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...core.config import settings


class AudioAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)
        self.llm_timeout_sec = 180

        # Initialize PostgreSQL engine for audio data
        try:
            self.engine = create_engine(settings.DATABASE_URL)
            self.logger.info("PostgreSQL connection initialized for audio data")
        except Exception as e:
            self.engine = None
            self.logger.error(f"Failed to initialize PostgreSQL: {e}")

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
        """Query audio_files metadata and extract tone analysis from database."""
        file_key = params.get("file_key")
        company_name = params.get("company_name")
        
        if not (file_key or company_name):
            raise ValueError("analyze_audio_tone requires 'file_key' or 'company_name'")
        
        try:
            audio_records = self._query_audio_files(file_key, company_name)
            
            if not audio_records:
                return {
                    "segments": [],
                    "overall_tone": "unknown",
                    "confidence_in_analysis": 0.0,
                }
            
            # Extract tone analysis from metadata
            latest_audio = audio_records[0]
            metadata = latest_audio.get("metadata", {})
            tone_analysis = metadata.get("tone_analysis", {})
            
            return {
                "segments": tone_analysis.get("segments", []),
                "overall_tone": tone_analysis.get("overall_tone", "neutral"),
                "confidence_in_analysis": tone_analysis.get("confidence", 0.0),
            }
        except Exception as exc:
            raise RuntimeError(f"Audio tone analysis failed: {exc}") from exc

    def detect_deception_markers(self, params: Dict[str, Any], task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query audio_files metadata and extract deception markers from database."""
        file_key = params.get("file_key")
        company_name = params.get("company_name")
        
        if not (file_key or company_name):
            raise ValueError("detect_deception_markers requires 'file_key' or 'company_name'")
        
        try:
            audio_records = self._query_audio_files(file_key, company_name)
            
            if not audio_records:
                return {
                    "deception_markers": [],
                    "hedging_word_count": 0,
                    "topic_avoidance_count": 0,
                    "overall_deception_likelihood": 0.0,
                    "explanation": "No audio data found",
                }
            
            # Extract deception markers from metadata
            latest_audio = audio_records[0]
            metadata = latest_audio.get("metadata", {})
            deception_analysis = metadata.get("deception_analysis", {})
            
            return {
                "deception_markers": deception_analysis.get("markers", []),
                "hedging_word_count": deception_analysis.get("hedging_count", 0),
                "topic_avoidance_count": deception_analysis.get("avoidance_count", 0),
                "overall_deception_likelihood": deception_analysis.get("likelihood", 0.0),
                "explanation": deception_analysis.get("explanation", ""),
            }
        except Exception as exc:
            raise RuntimeError(f"Deception marker detection failed: {exc}") from exc

    # ---------------------------------------------------------------
    # Internal helper: query audio_files table
    # ---------------------------------------------------------------
    def _query_audio_files(self, file_key: Optional[str] = None, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query audio_files table for company audio data."""
        if not self.engine:
            raise RuntimeError("PostgreSQL not initialized")
        
        try:
            with Session(self.engine) as session:
                query = """
                    SELECT id, company_name, call_type, period, file_key, 
                           duration_sec, transcript, participants, metadata, call_date
                    FROM audio_files
                    WHERE 1=1
                """
                params = {}
                
                if file_key:
                    query += " AND file_key = :file_key"
                    params["file_key"] = file_key
                
                if company_name:
                    query += " AND LOWER(company_name) = LOWER(:company)"
                    params["company"] = company_name
                
                query += " ORDER BY call_date DESC LIMIT 5"
                
                result = session.execute(text(query), params)
                rows = result.fetchall()
                return [{
                    "id": str(row[0]),
                    "company_name": row[1],
                    "call_type": row[2],
                    "period": row[3],
                    "file_key": row[4],
                    "duration_sec": row[5],
                    "transcript": row[6],
                    "participants": row[7] or [],
                    "metadata": row[8] or {},
                    "call_date": str(row[9]) if row[9] else None,
                } for row in rows]
        except Exception as exc:
            self.logger.error(f"Audio file query failed: {exc}")
            raise RuntimeError(f"Database query failed: {exc}") from exc

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

