"""Financial agent implementation aligned with contract specs.

This agent exposes contract-aligned tool handlers:
- analyze_balance_sheet
- calculate_financial_ratios
- detect_cash_flow_divergence
- detect_related_party_transactions

`process` expects a task dict of the shape:
{
    "tool": "analyze_balance_sheet" | "calculate_financial_ratios" | ...,
    "params": { ... }  # matches the contract for that tool
}
It routes to the corresponding handler and returns the tool's output dict.
"""

import json
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import text, create_engine
from sqlmodel import Session

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...shared.llm_portkey import get_portkey_client, PortkeyLLMError
from ...core.config import settings


class FinancialAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)
        
        # Initialize Portkey LLM client for analysis
        try:
            self.llm_client = get_portkey_client()
            self.logger.info("Portkey LLM client initialized for financial analysis")
        except PortkeyLLMError as e:
            self.logger.warning(f"Portkey not available: {e}. Analysis will be limited.")
            self.llm_client = None

        # Initialize PostgreSQL engine for financial data
        try:
            self.engine = create_engine(settings.DATABASE_URL)
            self.logger.info("PostgreSQL connection initialized for financial data")
        except Exception as e:
            self.engine = None
            self.logger.error(f"Failed to initialize PostgreSQL: {e}")

        self.tool_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "analyze_balance_sheet": self.analyze_balance_sheet,
            "calculate_financial_ratios": self.calculate_financial_ratios,
            "detect_cash_flow_divergence": self.detect_cash_flow_divergence,
            "detect_related_party_transactions": self.detect_related_party_transactions,
        }

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route the incoming task to the correct financial tool.

        Expected task keys: tool (str), params (dict).
        Raises ValueError for unknown tools or missing params.
        """

        tool_name = task.get("tool")
        params = task.get("params", {})

        if not tool_name:
            raise ValueError("FinancialAgent task missing 'tool'")
        if tool_name not in self.tool_map:
            raise ValueError(f"Unsupported financial tool: {tool_name}")
        if not isinstance(params, dict):
            raise ValueError("FinancialAgent task 'params' must be a dict")

        self.logger.debug("Running financial tool", extra={"tool": tool_name, "params": params})
        return self.tool_map[tool_name](params, task)

    # ---------------------------------------------------------------
    # Tool implementations (query database, not LLM)
    # ---------------------------------------------------------------
    def analyze_balance_sheet(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Query balance sheet data from financial_filings and analyze via LLM."""
        company = params.get("company_name")
        period = params.get("period")
        
        if not company:
            raise ValueError("company_name required")
        
        try:
            filings = self._query_financial_filings(company, "balancesheet", period)
            
            if not filings:
                return {
                    "status": "No balance sheet data found",
                    "analysis": "No balance sheet data available for analysis",
                    "anomalies": [],
                    "source_documents": [],
                }
            
            # Format documents for analysis
            documents = [
                {
                    "id": f.get("id"),
                    "content": f.get("content_chunk", ""),
                    "company": f.get("company_name"),
                    "period": f.get("period"),
                    "document_id": f.get("id"),
                }
                for f in filings[:3]
            ]
            
            # Use LLM to analyze
            analysis_prompt = """Analyze this balance sheet and provide:
1. Total assets, liabilities, and equity breakdown
2. Any unusual account balances or ratios
3. Changes from previous year if visible
4. Any red flags or anomalies
5. Overall financial health assessment"""
            
            llm_analysis = self._analyze_with_llm(documents, analysis_prompt)
            
            return {
                "status": f"Balance sheet analyzed for {company}",
                "summary": llm_analysis.get("summary", ""),
                "key_metrics": llm_analysis.get("key_metrics", []),
                "anomalies": llm_analysis.get("anomalies", []),
                "health_indicator": llm_analysis.get("health_indicator", "unknown"),
                "recommendations": llm_analysis.get("recommendations", []),
                "source_documents": [f.get("id") for f in filings],
            }
        except Exception as exc:
            raise RuntimeError(f"Balance sheet analysis failed: {exc}") from exc

    def calculate_financial_ratios(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Query financial ratios and analyze via LLM."""
        company = params.get("company_name")
        period = params.get("period")
        
        if not company:
            raise ValueError("company_name required")
        
        try:
            filings = self._query_financial_filings(company, "financialratios", period)
            
            if not filings:
                return {
                    "status": "No financial ratio data found",
                    "analysis": "No financial ratio data available for analysis",
                    "anomalies": [],
                    "source_documents": [],
                }
            
            # Format documents for analysis
            documents = [
                {
                    "id": f.get("id"),
                    "content": f.get("content_chunk", ""),
                    "company": f.get("company_name"),
                    "period": f.get("period"),
                    "document_id": f.get("id"),
                }
                for f in filings[:3]
            ]
            
            # Use LLM to analyze
            analysis_prompt = """Analyze these financial ratios and provide:
1. Key profitability, liquidity, and solvency ratios
2. Year-over-year trend analysis
3. Industry comparison insights if possible
4. Warning signs or concerning ratios
5. Overall company financial health score
6. Specific anomalies or unusual patterns"""
            
            llm_analysis = self._analyze_with_llm(documents, analysis_prompt)
            
            return {
                "status": f"Financial ratios analyzed for {company}",
                "summary": llm_analysis.get("summary", ""),
                "key_metrics": llm_analysis.get("key_metrics", []),
                "anomalies": llm_analysis.get("anomalies", []),
                "health_indicator": llm_analysis.get("health_indicator", "unknown"),
                "recommendations": llm_analysis.get("recommendations", []),
                "source_documents": [f.get("id") for f in filings],
            }
        except Exception as exc:
            raise RuntimeError(f"Financial ratio calculation failed: {exc}") from exc

    def detect_cash_flow_divergence(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Query cash flow statements and analyze for divergence via LLM."""
        company = params.get("company_name")
        period = params.get("period")
        
        if not company:
            raise ValueError("company_name required")
        
        try:
            filings = self._query_financial_filings(company, "cashflow", period)
            
            if not filings:
                return {
                    "status": "No cash flow data available",
                    "analysis": "No cash flow data available for analysis",
                    "divergence_detected": False,
                    "source_documents": [],
                }
            
            # Format documents for analysis
            documents = [
                {
                    "id": f.get("id"),
                    "content": f.get("content_chunk", ""),
                    "company": f.get("company_name"),
                    "period": f.get("period"),
                    "document_id": f.get("id"),
                }
                for f in filings[:3]
            ]
            
            # Use LLM to analyze
            analysis_prompt = """Analyze this cash flow statement and provide:
1. Operating, investing, and financing cash flows breakdown
2. Compare net income to operating cash flow - any divergence?
3. Cash flow quality assessment
4. Liquidity concerns or improvements
5. Identify any red flags in cash flow patterns
6. Sustainability of current cash flow trends"""
            
            llm_analysis = self._analyze_with_llm(documents, analysis_prompt)
            
            # Check if LLM detected divergence
            divergence_detected = "divergence" in llm_analysis.get("summary", "").lower() or len(llm_analysis.get("anomalies", [])) > 0
            
            return {
                "status": f"Cash flow analyzed for {company}",
                "summary": llm_analysis.get("summary", ""),
                "key_metrics": llm_analysis.get("key_metrics", []),
                "anomalies": llm_analysis.get("anomalies", []),
                "divergence_detected": divergence_detected,
                "health_indicator": llm_analysis.get("health_indicator", "unknown"),
                "recommendations": llm_analysis.get("recommendations", []),
                "source_documents": [f.get("id") for f in filings],
            }
        except Exception as exc:
            raise RuntimeError(f"Cash flow divergence detection failed: {exc}") from exc

    def detect_related_party_transactions(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Query consolidated statements and analyze for related party transactions via LLM."""
        company = params.get("company_name")
        period = params.get("period")
        
        if not company:
            raise ValueError("company_name required")
        
        try:
            filings = self._query_financial_filings(company, "consolidated", period)
            
            if not filings:
                return {
                    "status": "No consolidated data found",
                    "analysis": "No consolidated data available for analysis",
                    "related_party_transactions": [],
                    "source_documents": [],
                }
            
            # Format documents for analysis
            documents = [
                {
                    "id": f.get("id"),
                    "content": f.get("content_chunk", ""),
                    "company": f.get("company_name"),
                    "period": f.get("period"),
                    "document_id": f.get("id"),
                }
                for f in filings[:3]
            ]
            
            # Use LLM to analyze
            analysis_prompt = """Analyze this consolidated financial statement for related party transactions:
1. Identify any related party transactions disclosed
2. Assess materiality of related party transactions
3. Look for fair pricing concerns
4. Check for adequate disclosure
5. Identify any concerning related party relationships
6. Flag any governance red flags related to RPT"""
            
            llm_analysis = self._analyze_with_llm(documents, analysis_prompt)
            
            return {
                "status": f"Related party analysis completed for {company}",
                "summary": llm_analysis.get("summary", ""),
                "related_party_transactions": llm_analysis.get("key_metrics", []),
                "anomalies": llm_analysis.get("anomalies", []),
                "health_indicator": llm_analysis.get("health_indicator", "unknown"),
                "recommendations": llm_analysis.get("recommendations", []),
                "source_documents": [f.get("id") for f in filings],
            }
        except Exception as exc:
            raise RuntimeError(f"Related party transaction detection failed: {exc}") from exc

    # ---------------------------------------------------------------
    # LLM Analysis: Use Portkey to analyze financial documents
    # ---------------------------------------------------------------
    def _analyze_with_llm(self, documents: List[Dict], analysis_prompt: str) -> Dict[str, Any]:
        """Use LLM to analyze financial documents and extract insights."""
        if not self.llm_client or not documents:
            return {
                "analysis": "No LLM analysis available",
                "insights": [],
                "anomalies": [],
            }
        
        try:
            # Combine document content for analysis
            doc_text = "\n\n".join([
                f"[{doc.get('company')} - {doc.get('document_id', 'unknown')}]:\n{doc.get('content', '')}"
                for doc in documents[:3]
            ])
            
            # Create analysis prompt - Keep it simple and focused
            full_prompt = f"""{analysis_prompt}

FINANCIAL DOCUMENTS TO ANALYZE:
{doc_text}

ANALYSIS INSTRUCTIONS:
You MUST respond with ONLY valid JSON (nothing else, no markdown code blocks).
Use this exact format:
{{"summary": "Your analysis here", "key_metrics": ["metric1", "metric2"], "anomalies": ["anomaly1"] or [], "health_indicator": "healthy|warning|critical", "recommendations": ["rec1", "rec2"]}}"""
            
            self.logger.debug(f"Prompt length: {len(full_prompt)}")
            if len(full_prompt) > 3000:
                self.logger.warning(f"LARGE PROMPT: {len(full_prompt)} chars")
            self.logger.debug(f"Prompt (last 200): {full_prompt[-200:]}")
            
            # Call LLM via Portkey
            response = self.llm_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Respond with ONLY valid JSON - no markdown, no extra text."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=3000,  # Increased to give more room for responses
                temperature=0.3,  # Lower temperature for more consistent formatting
            )
            
            # Parse response - extract JSON from LLM response
            analysis_text = response.choices[0].message.content.strip()
            
            self.logger.debug(f"Raw response length: {len(analysis_text)}")
            if analysis_text:
                self.logger.debug(f"Response start: {analysis_text[:100]}")
                self.logger.debug(f"Response end: {analysis_text[-100:]}")
            
            # Step 1: Remove markdown code block wrappers  
            if '```' in analysis_text:
                # Find code block boundaries
                first_fence = analysis_text.find('```')
                if first_fence >= 0:
                    # Skip past the opening fence
                    start_pos = first_fence + 3
                    # Skip language identifier on same line
                    newline_pos = analysis_text.find('\n', start_pos)
                    if newline_pos >= 0:
                        start_pos = newline_pos + 1
                    
                    # Find closing fence
                    closing_fence = analysis_text.find('```', start_pos)
                    if closing_fence >= 0:
                        analysis_text = analysis_text[start_pos:closing_fence].strip()
                        self.logger.debug(f"After markdown removal length: {len(analysis_text)}")
                        self.logger.debug(f"After markdown removal (first 300): {analysis_text[:300]}")
            
            # Step 2: Try standard JSON parsing
            analysis_json = None
            try:
                analysis_json = json.loads(analysis_text)
                self.logger.debug("Standard JSON parsing succeeded")
            except json.JSONDecodeError as e:
                self.logger.debug(f"Standard JSON parsing failed: {str(e)[:100]}")
                # Try fixing by escaping literal newlines in the JSON
                try:
                    import re
                    # Strategy: Find all quoted strings (allowing for newlines) and escape internal newlines
                    # Use DOTALL flag to make . match newlines, but we need a different approach
                    # Instead, manually iterate through and escape newlines within quotes
                    fixed_text = ""
                    in_string = False
                    i = 0
                    while i < len(analysis_text):
                        char = analysis_text[i]
                        
                        if char == '"' and (i == 0 or analysis_text[i-1] != '\\'):
                            in_string = not in_string
                            fixed_text += char
                        elif in_string and char == '\n':
                            # Newline inside a string - escape it
                            fixed_text += '\\n'
                        elif in_string and char == '\r':
                            fixed_text += '\\r'
                        elif in_string and char == '\t':
                            fixed_text += '\\t'
                        else:
                            fixed_text += char
                        i += 1
                    
                    analysis_json = json.loads(fixed_text)
                    self.logger.debug("Manual-escaped JSON parsing succeeded")
                except (json.JSONDecodeError, Exception):
                    self.logger.debug("Manual-escaped parsing failed, trying one-line")
                    
                    # Fallback: replace all newlines with spaces
                    try:
                        one_line_text = analysis_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        one_line_text = ' '.join(one_line_text.split())
                        analysis_json = json.loads(one_line_text)
                        self.logger.debug("One-line JSON parsing succeeded")
                    except json.JSONDecodeError as e2:
                        self.logger.debug(f"One-line JSON parsing failed: {str(e2)[:100]}")
            
            # Step 3: If that fails, try to clean up and parse
            if analysis_json is None:
                # Try removing leading/trailing whitespace and parse again
                cleaned = analysis_text.strip()
                try:
                    analysis_json = json.loads(cleaned)
                    self.logger.debug("Cleaned JSON parsing succeeded")
                except json.JSONDecodeError:
                    self.logger.debug("Cleaned JSON parsing failed")
                    # Try extracting just the JSON core from first { to last }
                    start_idx = cleaned.find('{')
                    end_idx = cleaned.rfind('}')
                    self.logger.debug(f"Found braces at: {start_idx} to {end_idx} (length: {end_idx - start_idx + 1 if start_idx >= 0 and end_idx >= 0 else 'N/A'})")
                    
                    if start_idx >= 0 and end_idx > start_idx:
                        try:
                            extracted_json = cleaned[start_idx:end_idx + 1]
                            self.logger.debug(f"Extracted JSON (first 200): {extracted_json[:200]}")
                            analysis_json = json.loads(extracted_json)
                            self.logger.debug("Extracted JSON parsing succeeded")
                        except json.JSONDecodeError as e:
                            self.logger.debug(f"Extracted JSON parsing failed: {str(e)[:100]}")
            
            # Step 4: Ultimate fallback - lenient parsing
            if analysis_json is None:
                self.logger.warning("JSON parsing failed, using lenient extraction")
                self.logger.debug(f"Lenient parsing input (first 500): {analysis_text[:500]}")
                analysis_json = self._parse_json_leniently(analysis_text)
                self.logger.debug(f"Lenient parsed result: {analysis_json}")
            
            # Ensure all required fields exist
            if analysis_json:
                analysis_json.setdefault("summary", "")
                analysis_json.setdefault("key_metrics", [])
                analysis_json.setdefault("anomalies", [])
                analysis_json.setdefault("health_indicator", "unknown")
                analysis_json.setdefault("recommendations", [])
            else:
                # Last resort fallback
                analysis_json = {
                    "summary": analysis_text[:500],
                    "key_metrics": [],
                    "anomalies": [],
                    "health_indicator": "unknown",
                    "recommendations": []
                }
            
            return analysis_json
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {
                "analysis": f"LLM analysis failed: {str(e)}",
                "anomalies": [],
                "health_indicator": "unknown"
            }

    # ---------------------------------------------------------------
    # Internal helper: lenient JSON parser for malformed responses
    # ---------------------------------------------------------------
    def _parse_json_leniently(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON fields from text that doesn't parse as valid JSON.
        Uses regex-like string parsing to extract field values.
        """
        import re
        
        result = {
            "summary": "",
            "key_metrics": [],
            "anomalies": [],
            "health_indicator": "unknown",
            "recommendations": []
        }
        
        self.logger.debug(f"Lenient parsing: text length = {len(text)}")
        
        # Extract summary using regex - match "summary": "..." (with any content including newlines)
        summary_pattern = r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'
        summary_match = re.search(summary_pattern, text)
        if summary_match:
            summary_text = summary_match.group(1)
            # Unescape common sequences
            summary_text = summary_text.replace('\\n', ' ').replace('\\t', ' ').replace('\\r', ' ')
            result["summary"] = summary_text.strip()
            self.logger.debug(f"Extracted summary via regex: {result['summary'][:80]}")
        
        # If regex fails, try simple extraction
        if not result["summary"]:
            # Find "summary": and extract everything up to the next field or }
            summary_idx = text.find('"summary"')
            if summary_idx >= 0:
                colon_idx = text.find(':', summary_idx)
                if colon_idx >= 0:
                    # Find the first quote after colon
                    first_quote = text.find('"', colon_idx)
                    if first_quote >= 0:
                        # Collect until we find a quote followed by comma or }
                        content = ""
                        idx = first_quote + 1
                        while idx < len(text):
                            if text[idx:idx+2] == '\\n':
                                content += ' '
                                idx += 2
                            elif text[idx] == '"':
                                # Check if this ends the string (followed by comma or })
                                next_chars = text[idx+1:idx+5].lstrip()
                                if next_chars.startswith(',') or next_chars.startswith('}'):
                                    result["summary"] = content.strip()
                                    self.logger.debug(f"Extracted summary via simple: {result['summary'][:80]}")
                                    break
                                else:
                                    content += text[idx]
                            elif text[idx] in '\n\r\t':
                                content += ' '
                            else:
                                content += text[idx]
                            idx += 1
        
        # Extract health_indicator
        health_pattern = r'"health_indicator"\s*:\s*"([^"]*)"'
        health_match = re.search(health_pattern, text)
        if health_match:
            health_text = health_match.group(1).lower().strip()
            if health_text in ['healthy', 'warning', 'critical']:
                result["health_indicator"] = health_text
                self.logger.debug(f"Extracted health_indicator: {result['health_indicator']}")
        
        # Extract arrays
        for field in ['key_metrics', 'anomalies', 'recommendations']:
            result[field] = self._extract_array_field(text, field)
        
        return result
    
    def _extract_array_field(self, text: str, field_name: str) -> List[str]:
        """Extract an array field from text that might not be valid JSON."""
        field_search = f'"{field_name}"'
        match = text.find(field_search)
        if match < 0:
            return []
        
        # Find the opening [
        bracket_pos = text.find('[', match)
        if bracket_pos < 0:
            return []
        
        # Find the closing ] - need to be careful with nested structures
        closing_bracket = -1
        bracket_count = 1
        search_pos = bracket_pos + 1
        in_string = False
        
        while search_pos < len(text) and bracket_count > 0:
            char = text[search_pos]
            if char == '"' and (search_pos == 0 or text[search_pos - 1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        closing_bracket = search_pos
                        break
            search_pos += 1
        
        if closing_bracket < 0:
            return []
        
        # Extract the array content
        array_content = text[bracket_pos + 1:closing_bracket]
        
        # Parse array items more carefully
        items = []
        current_item = ""
        in_string = False
        escape_next = False
        
        for char in array_content:
            if escape_next:
                current_item += char
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"':
                if not escape_next:
                    in_string = not in_string
                    if in_string:
                        # Start of quoted string - capture everything until closing quote
                        current_item = ""
                    else:
                        # End of quoted string - save it
                        if current_item.strip():
                            items.append(current_item.strip())
                        current_item = ""
                else:
                    current_item += char
            elif char == ',' and not in_string:
                # Item separator
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ""
            elif in_string:
                # Inside a quoted string - capture everything
                current_item += char
            elif char not in ' \n\t\r':
                # Outside string, capture non-whitespace
                current_item += char
        
        # Add the last item
        if current_item.strip():
            items.append(current_item.strip())
        
        return items

    # ---------------------------------------------------------------
    # Internal helper: query financial_filings table
    # ---------------------------------------------------------------
    def _query_financial_filings(self, company_name: str, doc_type: str, period: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query financial_filings table for company data."""
        if not self.engine:
            raise RuntimeError("PostgreSQL not initialized")
        
        try:
            with Session(self.engine) as session:
                query = """
                    SELECT id, company_name, company_ticker, period, doc_type, 
                           content_chunk, metadata, filing_date
                    FROM financial_filings
                    WHERE LOWER(company_name) = LOWER(:company) 
                    AND LOWER(doc_type) = LOWER(:doc_type)
                """
                params = {"company": company_name, "doc_type": doc_type}
                
                if period:
                    query += " AND period = :period"
                    params["period"] = period
                
                query += " ORDER BY filing_date DESC LIMIT 5"
                
                result = session.execute(text(query), params)
                rows = result.fetchall()
                return [{"id": str(row[0]), "company_name": row[1], "company_ticker": row[2], "period": row[3], "doc_type": row[4], "content_chunk": row[5], "metadata": row[6] or {}, "filing_date": str(row[7]) if row[7] else None} for row in rows]
        except Exception as exc:
            self.logger.error(f"Financial filing query failed: {exc}")
            raise RuntimeError(f"Database query failed: {exc}") from exc
