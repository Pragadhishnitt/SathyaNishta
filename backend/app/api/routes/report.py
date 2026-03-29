from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
import json
from sqlalchemy import create_engine, text
from sqlmodel import Session
from app.core.config import settings
from app.shared.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)
engine = create_engine(settings.DATABASE_URL)


def _escape_text(value) -> str:
    text_value = "" if value is None else str(value)
    return text_value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _add_agent_section(elements, styles, header_style, subsection_style, body_style, title: str, findings: dict | None):
    elements.append(Paragraph(title, header_style))

    if not isinstance(findings, dict) or not findings:
        elements.append(Paragraph("No agent findings recorded.", body_style))
        return

    risk_score = findings.get("risk_score")
    if risk_score is not None:
        elements.append(Paragraph(f"<b>Risk Score:</b> {_escape_text(risk_score)}/10", body_style))

    summary_items = findings.get("findings") or []
    if isinstance(summary_items, list) and summary_items:
        elements.append(Paragraph("Key Findings", subsection_style))
        for item in summary_items[:8]:
            elements.append(Paragraph(f"• {_escape_text(item)}", body_style))
    else:
        elements.append(Paragraph("No detailed findings recorded.", body_style))

    evidence_map = findings.get("evidence") or {}
    if isinstance(evidence_map, dict) and evidence_map:
        elements.append(Paragraph("Supporting Data", subsection_style))
        for key, value in list(evidence_map.items())[:10]:
            label = _escape_text(str(key).replace("_", " ").title())
            elements.append(Paragraph(f"<b>{label}:</b> {_escape_text(value)}", body_style))

    elements.append(Spacer(1, 10))


@router.get("/investigate/{inv_id}/report")
async def generate_report(inv_id: str):
    """Generate a professional PDF report for a completed investigation."""
    _logger.info(f"Generating PDF report for investigation {inv_id}")

    # 1. Fetch data from DB
    try:
        with Session(engine) as session:
            # Get main investigation data
            inv = session.execute(text("SELECT * FROM investigations WHERE id = :id"), {"id": inv_id}).fetchone()

            if not inv:
                _logger.warning(f"Report generation failed: investigation {inv_id} not found")
                raise HTTPException(status_code=404, detail="Investigation not found")

            if inv.status != "completed":
                _logger.warning(f"Report generation blocked: investigation {inv_id} has status={inv.status}")
                raise HTTPException(status_code=400, detail="Investigation not yet completed")

            # Get synthesis evidence from audit trail
            audit = session.execute(
                text(
                    "SELECT output_payload FROM audit_trails WHERE investigation_id = :id AND step_type = 'synthesis'"
                ),
                {"id": inv_id},
            ).fetchone()

            evidence = []
            payload = {}
            if audit:
                raw_payload = audit.output_payload
                if isinstance(raw_payload, (str, bytes, bytearray)):
                    payload = json.loads(raw_payload)
                elif isinstance(raw_payload, dict):
                    payload = raw_payload
                else:
                    raise TypeError(f"Unsupported audit payload type: {type(raw_payload).__name__}")
                evidence = payload.get("evidence", [])
                _logger.info(f"Loaded synthesis audit for {inv_id}: evidence_count={len(evidence)}")
            else:
                _logger.warning(f"No synthesis audit row found for investigation {inv_id}")

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Failed to fetch report data for {inv_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch report data")

    # 2. Extract company name (usually from query or first finding)
    company_name = "Unknown Company"
    if evidence:
        # Synthesis payload as per investigate.py doesn't have company_name,
        # but the main page usually sets it.
        # For now, let's try to extract from the query again or just use a generic title.
        pass

    # Let's try to find company name in evidence if possible
    # (Actually investigate.py stores company_name in the in-memory _results,
    # but that's volatile. For the report, we'll use the query or a best-effort extraction)
    from app.api.routes.investigate import _extract_company_name

    company_name = _extract_company_name(inv.query)

    # 3. Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Heading1"], fontSize=24, spaceAfter=20, textColor=colors.HexColor("#0f172a")
    )
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Heading2"],
        fontSize=16,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor("#1e293b"),
    )
    subsection_style = ParagraphStyle(
        "SubsectionStyle",
        parent=styles["Heading3"],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor("#334155"),
    )
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=13, spaceAfter=4)

    elements = []

    # Header section
    elements.append(Paragraph("SathyaNishta Forensic Report", title_style))
    elements.append(Paragraph(f"<b>Target:</b> {company_name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Investigation ID:</b> {inv_id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {inv.completed_at.strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Verdict Box
    verdict = inv.verdict or "UNKNOWN"
    score = inv.fraud_risk_score or 0.0

    verdict_color = colors.red if score >= 8 else colors.orange if score >= 4 else colors.green

    data = [
        [
            Paragraph(f"<b>FRAUD RISK SCORE: {score}/10</b>", styles["Heading3"]),
            Paragraph(f"<b>VERDICT: {verdict}</b>", styles["Heading3"]),
        ]
    ]
    t = Table(data, colWidths=[200, 200])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), verdict_color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Evidence Matrix
    elements.append(Paragraph("Synthesized Evidence Matrix", header_style))

    if evidence:
        table_data = [["Source", "Finding", "Severity"]]
        for ev in evidence:
            table_data.append(
                [ev.get("source", "N/A"), Paragraph(ev.get("finding", ""), styles["Normal"]), ev.get("severity", "N/A")]
            )

        et = Table(table_data, colWidths=[80, 320, 60])
        et.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(et)
    else:
        elements.append(Paragraph("No specific evidence findings recorded.", styles["Normal"]))

    agent_sections = [
        ("Financial Agent Output", payload.get("financial_findings")),
        ("Graph Agent Output", payload.get("graph_findings")),
        ("Compliance Agent Output", payload.get("compliance_findings")),
        ("Audio Agent Output", payload.get("audio_findings")),
        ("News Agent Output", payload.get("news_findings")),
    ]
    for section_title, findings in agent_sections:
        _add_agent_section(elements, styles, header_style, subsection_style, body_style, section_title, findings)

    # Footer
    elements.append(Spacer(1, 40))
    elements.append(
        Paragraph(
            "<i>This report is generated by MarketChatGPT (by ET) forensic agents. Information is based on real-time market data, regulatory filings, and graph analysis.</i>",
            styles["Italic"],
        )
    )

    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()

    filename = f"SathyaNishta_Report_{company_name.replace(' ', '_')}_{inv_id[:8]}.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
