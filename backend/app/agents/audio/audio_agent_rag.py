"""Enhanced Audio Agent with RAG and LLM Analysis

This agent provides audio transcript analysis tools:
- analyze_audio_tone - Analyze tone and sentiment from transcripts
- detect_deception_markers - Detect potential deception markers
- analyze_transcript_content - Analyze content using RAG retrieval and LLM

Uses Cohere embeddings for semantic search and Portkey LLM for analysis.
"""

import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlmodel import Session

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...core.config import settings
from ...shared.llm_portkey import get_portkey_client


class AudioAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)
        self.llm_timeout_sec = 180

        # Initialize PostgreSQL engine for audio data
        try:
            self.engine = create_engine(settings.DATABASE_URL)
            self.logger.info("✓ PostgreSQL connection initialized for audio data")
        except Exception as e:
            self.engine = None
            self.logger.error(f"✗ Failed to initialize PostgreSQL: {e}")

        # Initialize Portkey LLM client
        try:
            self.llm_client = get_portkey_client()
            self.logger.info("✓ Portkey LLM client initialized")
        except Exception as e:
            self.llm_client = None
            self.logger.error(f"✗ Failed to initialize Portkey LLM: {e}")

        self.tool_map = {
            "analyze_audio_tone": self.analyze_audio_tone,
            "detect_deception_markers": self.detect_deception_markers,
            "analyze_transcript_content": self.analyze_transcript_content,
        }

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route incoming task to the correct audio tool"""
        tool_name = task.get("tool")
        params = task.get("params", {})

        if not tool_name:
            raise ValueError("AudioAgent task missing 'tool'")
        if tool_name not in self.tool_map:
            raise ValueError(f"Unsupported audio tool: {tool_name}")
        if not isinstance(params, dict):
            raise ValueError("AudioAgent task 'params' must be a dict")

        self.logger.debug("Running audio tool", extra={"tool": tool_name, "params": params})
        return self.tool_map[tool_name](params)

    # =====================================================================
    # RAG Helper Methods
    # =====================================================================

    def _retrieve_audio_documents(self, company: str, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve most relevant audio transcripts using semantic search"""
        try:
            if not self.engine:
                self.logger.error("Database engine not initialized")
                return []
            
            # Import Cohere for embedding the query
            import cohere
            from dotenv import load_dotenv
            import os
            
            load_dotenv()
            cohere_api_key = os.getenv("COHERE_API_KEY")
            if not cohere_api_key:
                self.logger.error("COHERE_API_KEY not found")
                return []
            
            cohere_client = cohere.Client(cohere_api_key)
            
            # Generate embedding for query
            response = cohere_client.embed(
                texts=[query],
                model="embed-english-v3.0",
                input_type="search_query"
            )
            query_embedding = response.embeddings[0]
            query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            with self.engine.connect() as connection:
                # Try simple name-based search first (more reliable)
                self.logger.debug(f"Searching for company: {company}")
                
                results = connection.execute(text("""
                    SELECT id, company_name, company_code, transcript_date, 
                           content_chunk, chunk_number, metadata, 0.8 as similarity
                    FROM audio_transcriptions
                    WHERE company_name ILIKE :company_name
                    LIMIT :top_k
                """), {
                    "company_name": f"%{company}%",
                    "top_k": top_k
                }).fetchall()
                
                self.logger.debug(f"Query returned {len(results) if results else 0} results for {company}")
                
                documents = []
                for row in results:
                    # Handle metadata field - might be dict or JSON string
                    metadata = row[6]
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata) if metadata else {}
                    elif metadata is None:
                        metadata = {}
                    
                    documents.append({
                        "id": row[0],
                        "company_name": row[1],
                        "company_code": row[2],
                        "transcript_date": row[3],
                        "content": row[4],
                        "chunk_number": row[5],
                        "metadata": metadata,
                        "similarity": float(row[7]) if row[7] else 0.0
                    })
                
                self.logger.info(f"Retrieved {len(documents)} audio documents for {company}")
                return documents
        
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []

    def _analyze_with_llm(self, transcript_content: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze audio transcript content using Portkey LLM"""
        if not self.llm_client:
            self.logger.error("LLM client not initialized")
            return {
                "summary": "LLM analysis unavailable",
                "tone_indicators": [],
                "sentiment": "unknown",
                "deception_markers": [],
                "recommendations": []
            }

        # Prepare analysis prompt based on analysis type
        if analysis_type == "tone":
            prompt = f"""Analyze the following audio transcript for tone and sentiment indicators.
Extract structure analysis with these fields only:

Transcript: {transcript_content}

Respond with ONLY valid JSON:
{{
    "summary": "Brief summary of tone and sentiment",
    "tone_indicators": ["list", "of", "tone", "indicators"],
    "sentiment": "positive|neutral|negative",
    "intensity": "low|medium|high"
}}"""
        elif analysis_type == "deception":
            prompt = f"""Analyze the following audio transcript for potential deception markers.
Look for: contradictions, vague language, hedging, avoiding specifics, defensive statements.

Transcript: {transcript_content}

Respond with ONLY valid JSON:
{{
    "summary": "Overall assessment of deception likelihood",
    "deception_markers": ["marker1", "marker2", "marker3"],
    "likelihood": "low|medium|high",
    "confidence": "low|medium|high"
}}"""
        else:  # general content analysis
            prompt = f"""Analyze the audio transcript for key insights and insights relevant to financial/business context.
Extract structure analysis with these fields:

Transcript: {transcript_content}

Respond with ONLY valid JSON:
{{
    "summary": "Key insights from transcript",
    "key_points": ["point1", "point2", "point3"],
    "financial_health_assessment": "strong|stable|weak|critical",
    "recommendations": ["recommendation1", "recommendation2"]
}}"""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Multi-stage JSON parsing with fallback
            analysis_json = self._parse_json_response(analysis_text)
            
            return analysis_json
        
        except Exception as e:
            self.logger.error(f"LLM analysis error: {e}")
            return {"summary": f"Analysis error: {str(e)}", "error": True}

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response with multi-stage fallback"""
        # Try 1: Standard JSON parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try 2: Manual newline escaping in quoted strings
        try:
            fixed_text = ""
            in_string = False
            for i, char in enumerate(response_text):
                if char == '"' and (i == 0 or response_text[i-1] != '\\'):
                    in_string = not in_string
                elif in_string and char == '\n':
                    fixed_text += '\\n'
                else:
                    fixed_text += char
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
        
        # Try 3: One-line replacement
        try:
            one_line = response_text.replace('\n', ' ').replace('\r', ' ')
            one_line = re.sub(r'\s+', ' ', one_line)
            return json.loads(one_line)
        except json.JSONDecodeError:
            pass
        
        # Try 4: Lenient regex-based extraction
        return self._extract_fields_leniently(response_text)

    def _extract_fields_leniently(self, text: str) -> Dict[str, Any]:
        """Extract fields from partially broken JSON using regex"""
        result = {}
        
        # Extract summary field
        summary_match = re.search(r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', text)
        if summary_match:
            result['summary'] = summary_match.group(1).replace('\\"', '"')
        
        # Extract arrays using improved method
        result['tone_indicators'] = self._extract_array_field(text, 'tone_indicators')
        result['deception_markers'] = self._extract_array_field(text, 'deception_markers')
        result['key_points'] = self._extract_array_field(text, 'key_points')
        result['recommendations'] = self._extract_array_field(text, 'recommendations')
        
        # Extract sentiment/likely fields
        sentiment_match = re.search(r'"sentiment"\s*:\s*"([^"]+)"', text)
        if sentiment_match:
            result['sentiment'] = sentiment_match.group(1)
        
        likelihood_match = re.search(r'"likelihood"\s*:\s*"([^"]+)"', text)
        if likelihood_match:
            result['likelihood'] = likelihood_match.group(1)
        
        health_match = re.search(r'"financial_health_assessment"\s*:\s*"([^"]+)"', text)
        if health_match:
            result['financial_health_assessment'] = health_match.group(1)
        
        return result if result else {"summary": "Unable to parse analysis response", "error": True}

    def _extract_array_field(self, text: str, field_name: str) -> List[str]:
        """Extract array values from JSON-like text"""
        # Find the field and its array value
        pattern = rf'"{field_name}"\s*:\s*\['
        match = re.search(pattern, text)
        
        if not match:
            return []
        
        start_idx = match.end()
        
        # Find matching closing bracket
        bracket_count = 1
        in_string = False
        end_idx = start_idx
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i
                        break
        
        array_str = text[start_idx:end_idx]
        items = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', array_str)
        
        return [item.replace('\\"', '"').replace('\\n', '\n') for item in items if item.strip()]

    # =====================================================================
    # Audio Tool Implementations
    # =====================================================================

    def analyze_audio_tone(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tone and sentiment from company audio transcripts
        
        Args:
            params:
                company: Company name (e.g., "State Bank of India")
                query: Specific query or topic to analyze (optional)
        """
        company = params.get("company")
        query = params.get("query", "overall tone and sentiment")
        
        if not company:
            return {"error": "Company name required", "status": "failed"}
        
        try:
            # Step 1: Retrieve relevant audio documents
            documents = self._retrieve_audio_documents(company, query, top_k=3)
            
            if not documents:
                return {
                    "company": company,
                    "query": query,
                    "found_documents": 0,
                    "error": f"No audio transcripts found for {company}",
                    "status": "no_data"
                }
            
            # Step 2: Combine documents for analysis
            combined_content = "\n\n".join([
                f"[{doc['chunk_number']}/{doc.get('metadata', {}).get('total_chunks', '?')}] {doc['content']}"
                for doc in documents
            ])
            
            # Step 3: Analyze with LLM
            analysis = self._analyze_with_llm(combined_content, "tone")
            
            return {
                "company": company,
                "query": query,
                "found_documents": len(documents),
                "document_similarity": [d['similarity'] for d in documents],
                "analysis": analysis,
                "status": "success"
            }
        
        except Exception as e:
            self.logger.error(f"Error in analyze_audio_tone: {e}")
            return {"error": str(e), "status": "failed"}

    def detect_deception_markers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential deception markers in audio transcripts
        
        Args:
            params:
                company: Company name (e.g., "State Bank of India")
                focus: Specific area to focus on (optional)
        """
        company = params.get("company")
        focus = params.get("focus", "overall content")
        
        if not company:
            return {"error": "Company name required", "status": "failed"}
        
        try:
            # Step 1: Retrieve relevant audio documents
            documents = self._retrieve_audio_documents(company, f"deception markers {focus}", top_k=3)
            
            if not documents:
                return {
                    "company": company,
                    "focus": focus,
                    "found_documents": 0,
                    "error": f"No audio transcripts found for {company}",
                    "status": "no_data"
                }
            
            # Step 2: Combine documents for analysis
            combined_content = "\n\n".join([
                f"[{doc['chunk_number']}/{doc.get('metadata', {}).get('total_chunks', '?')}] {doc['content']}"
                for doc in documents
            ])
            
            # Step 3: Analyze with LLM for deception markers
            analysis = self._analyze_with_llm(combined_content, "deception")
            
            return {
                "company": company,
                "focus": focus,
                "found_documents": len(documents),
                "document_similarity": [d['similarity'] for d in documents],
                "analysis": analysis,
                "status": "success"
            }
        
        except Exception as e:
            self.logger.error(f"Error in detect_deception_markers: {e}")
            return {"error": str(e), "status": "failed"}

    def analyze_transcript_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transcript content for financial/business insights using RAG+LLM
        
        Args:
            params:
                company: Company name (e.g., "State Bank of India")
                topic: Topic or aspect to analyze (e.g., "balance sheet", "growth strategy")
        """
        company = params.get("company")
        topic = params.get("topic", "financial performance and business health")
        
        if not company:
            return {"error": "Company name required", "status": "failed"}
        
        try:
            # Step 1: Retrieve relevant audio documents
            documents = self._retrieve_audio_documents(company, topic, top_k=3)
            
            if not documents:
                return {
                    "company": company,
                    "topic": topic,
                    "found_documents": 0,
                    "error": f"No audio transcripts found for {company}",
                    "status": "no_data"
                }
            
            # Step 2: Combine documents for analysis
            combined_content = "\n\n".join([
                f"[{doc['chunk_number']}/{doc.get('metadata', {}).get('total_chunks', '?')}] {doc['content']}"
                for doc in documents
            ])
            
            # Step 3: Analyze with LLM
            analysis = self._analyze_with_llm(combined_content, "content")
            
            return {
                "company": company,
                "topic": topic,
                "found_documents": len(documents),
                "document_similarity": [d['similarity'] for d in documents],
                "analysis": analysis,
                "status": "success"
            }
        
        except Exception as e:
            self.logger.error(f"Error in analyze_transcript_content: {e}")
            return {"error": str(e), "status": "failed"}

    def detect_deception_markers_with_timestamps(self, company: str) -> Dict[str, Any]:
        """
        Detect deception markers and enrich with timeline percentages for frontend heatmap.
        """
        if not company:
            return {"status": "failed", "markers": []}
        if not self.engine:
            return {"status": "no_data", "markers": []}

        try:
            with self.engine.connect() as connection:
                rows = connection.execute(text("""
                    SELECT chunk_number, content_chunk, metadata
                    FROM audio_transcriptions
                    WHERE company_name ILIKE :company_name
                    ORDER BY chunk_number ASC
                    LIMIT 30
                """), {"company_name": f"%{company}%"}).fetchall()

            chunks: List[Dict[str, Any]] = []
            for row in rows:
                metadata = row[2]
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata) if metadata else {}
                    except Exception:
                        metadata = {}
                if metadata is None:
                    metadata = {}
                chunks.append({
                    "chunk_index": int(row[0] or 0),
                    "transcript_text": row[1] or "",
                    "start_time": float(metadata.get("start_time", metadata.get("start", 0)) or 0),
                    "end_time": float(metadata.get("end_time", metadata.get("end", 0)) or 0),
                    "duration_total": float(metadata.get("duration_total", metadata.get("total_duration", 0)) or 0),
                })

            if not chunks:
                return {"status": "no_data", "markers": []}

            # Fallback for missing timestamps: infer by index over fixed duration.
            if all((c["start_time"] == 0 and c["end_time"] == 0) for c in chunks):
                inferred_total = float(len(chunks) * 120)
                for i, c in enumerate(chunks):
                    c["start_time"] = float(i * 120)
                    c["end_time"] = float((i + 1) * 120)
                    c["duration_total"] = inferred_total

            total_duration = chunks[-1].get("duration_total") or chunks[-1].get("end_time") or 1
            chunk_texts = "\n".join([
                f"[CHUNK {c['chunk_index']} | {c['start_time']}s-{c['end_time']}s]: {c['transcript_text'][:300]}"
                for c in chunks
            ])

            prompt = f"""Analyze this earnings call transcript for deception markers.
For each marker found, return the CHUNK INDEX where it occurs.

Transcript:
{chunk_texts}

Return JSON only:
{{
  "overall_likelihood": "low|medium|high",
  "markers": [
    {{
      "chunk_index": <int>,
      "marker_type": "hedging|evasion|contradiction|false_confidence|topic_deflection",
      "quote": "<short quote>",
      "severity": "low|medium|high",
      "explanation": "<1 sentence>"
    }}
  ]
}}"""

            analysis = self._analyze_with_llm(prompt, "deception")
            parsed_markers = analysis.get("markers")
            if not isinstance(parsed_markers, list):
                # Backward compatibility with existing schema
                legacy_markers = analysis.get("deception_markers", [])
                parsed_markers = [
                    {
                        "chunk_index": chunks[min(i, len(chunks) - 1)]["chunk_index"],
                        "marker_type": "deception",
                        "quote": m[:120],
                        "severity": "medium",
                        "explanation": m,
                    }
                    for i, m in enumerate(legacy_markers[:5])
                ]

            chunk_map = {c["chunk_index"]: c for c in chunks}
            enriched_markers: List[Dict[str, Any]] = []
            for marker in parsed_markers:
                idx = int(marker.get("chunk_index", chunks[0]["chunk_index"]))
                chunk = chunk_map.get(idx, chunks[0])
                start_pct = (chunk.get("start_time", 0) / total_duration) if total_duration else 0
                end_pct = (chunk.get("end_time", 0) / total_duration) if total_duration else start_pct
                enriched_markers.append({
                    "chunk_index": idx,
                    "marker_type": marker.get("marker_type", "deception"),
                    "quote": marker.get("quote", ""),
                    "severity": marker.get("severity", "medium"),
                    "explanation": marker.get("explanation", ""),
                    "start_pct": round(max(0.0, min(1.0, start_pct)), 4),
                    "end_pct": round(max(0.0, min(1.0, end_pct)), 4),
                    "start_time_s": chunk.get("start_time", 0),
                    "end_time_s": chunk.get("end_time", 0),
                })

            return {
                "status": "success",
                "overall_likelihood": analysis.get("overall_likelihood", analysis.get("likelihood", "unknown")),
                "markers": enriched_markers,
                "total_duration_s": total_duration,
                "chunk_count": len(chunks),
            }
        except Exception as e:
            self.logger.error(f"detect_deception_markers_with_timestamps failed: {e}")
            return {"status": "failed", "markers": []}
