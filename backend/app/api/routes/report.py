import json
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
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


def _add_agent_section(
    elements,
    styles,
    header_style,
    subsection_style,
    body_style,
    title: str,
    findings: dict | None,
):
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


@router.get("/report/test")
async def test_report_endpoint():
    """Test endpoint to verify report API is accessible."""
    return {"status": "ok", "message": "Report API is working"}


@router.get("/investigate/{inv_id}/report")
async def generate_report(inv_id: str):
    """Generate a high-fidelity, professional PDF report for a forensic investigation."""
    _logger.info(f"Generating Premium PDF report for investigation {inv_id}")

    # 1. Fetch data from DB
    try:
        with Session(engine) as session:
            inv = session.execute(text("SELECT * FROM investigations WHERE id = :id"), {"id": inv_id}).fetchone()

            if not inv:
                _logger.error(f"Investigation not found: {inv_id}")
                raise HTTPException(status_code=404, detail="Investigation not found")

            # Check audit for evidence
            audit = session.execute(
                text("SELECT output_payload FROM audit_trails WHERE investigation_id = :id AND step_type = 'synthesis'"),
                {"id": inv_id},
            ).fetchone()

            evidence = []
            payload = {}
            if audit:
                raw_payload = audit.output_payload
                try:
                    payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
                    evidence = payload.get("evidence", [])
                    _logger.info(f"Found {len(evidence)} evidence items for investigation {inv_id}")
                except json.JSONDecodeError as e:
                    _logger.error(f"Failed to parse audit payload: {e}")
            else:
                _logger.warning(f"No audit trail found for investigation {inv_id}")
            
    except Exception as e:
        _logger.error(f"Failed to fetch report data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report data")

    # 2. Extract company name and metadata
    from app.api.routes.investigate import _extract_company_name
    company_name = _extract_company_name(inv.query or "")
    # Use updated_at as the completion date
    date_str = inv.updated_at.strftime('%B %d, %Y at %I:%M %p') if inv.updated_at else "N/A"

    # 3. Create PDF
    _logger.info(f"Starting PDF generation for investigation {inv_id}")
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    # Premium Indigo Palette
    INDIGO = colors.HexColor("#6366f1")
    INDIGO_DARK = colors.HexColor("#4338ca")
    RED_ACCENT = colors.HexColor("#ef4444")
    GREEN_ACCENT = colors.HexColor("#10b981")
    SURFACE_LIGHT = colors.HexColor("#f8fafc")
    TEXT_MAIN = colors.HexColor("#0f172a")
    TEXT_MUTED = colors.HexColor("#64748b")

    # Custom Styles
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=28,
        spaceAfter=15,
        textColor=TEXT_MAIN,
        fontName="Helvetica-Bold",
    )
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Heading2"],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=12,
        textColor=INDIGO,
        fontName="Helvetica-Bold",
        borderPadding=(0, 0, 5, 0),
    )
    subsection_style = ParagraphStyle(
        "SubsectionStyle",
        parent=styles["Heading3"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        textColor=TEXT_MAIN,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=8, textColor=TEXT_MAIN)
    footer_style = ParagraphStyle("FooterStyle", parent=styles["Italic"], fontSize=8, alignment=1, textColor=TEXT_MUTED)

    elements = []

    # 1. Header (Logo/Title & Meta)
    elements.append(Paragraph("SathyaNishta", title_style))
    elements.append(Paragraph("Forensic Investigation Protocol — Evidence Brief", ParagraphStyle("Sub", fontSize=12, textColor=INDIGO, spaceAfter=20)))
    
    meta_data = [
        [Paragraph(f"<b>TARGET ENTITY:</b> {company_name}", body_style), Paragraph(f"<b>INVESTIGATION ID:</b> {inv_id[:12]}...", body_style)],
        [Paragraph(f"<b>STATUS:</b> {inv.status.upper()}", body_style), Paragraph(f"<b>GENERATED:</b> {date_str}", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[250, 250])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # 2. Verdict & Risk Score Section
    verdict = (inv.verdict or "CAUTION").upper()
    score = float(inv.fraud_risk_score or 0.0)
    score_color = RED_ACCENT if score >= 7.5 else GREEN_ACCENT if score < 4.0 else colors.orange

    verdict_data = [[
        Paragraph(f"<b>CRITICAL RISK SCORE</b><br/><font size=30><b>{score}/10.0</b></font>", ParagraphStyle("Score", alignment=1, textColor=colors.whitesmoke)),
        Paragraph(f"<b>FORENSIC VERDICT</b><br/><font size=24><b>{verdict}</b></font>", ParagraphStyle("Verdict", alignment=1, textColor=colors.whitesmoke))
    ]]
    vt = Table(verdict_data, colWidths=[250, 250])
    vt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), score_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('GRID', (0,0), (-1,-1), 1, colors.whitesmoke),
    ]))
    elements.append(vt)
    elements.append(Spacer(1, 25))

    # 3. Synthesized Evidence Matrix
    elements.append(Paragraph("Automated Evidence Matrix (Cross-Agent Correlation)", header_style))
    if evidence:
        table_data = [[Paragraph("<b>SOURCE</b>", body_style), Paragraph("<b>FINDINGS & ANOMALIES</b>", body_style), Paragraph("<b>SEVERITY</b>", body_style)]]
        for ev in evidence:
            sev_color = RED_ACCENT if ev.get("severity") == "HIGH" else INDIGO
            table_data.append([
                Paragraph(f"<b>{ev.get('source', '')}</b>", body_style),
                Paragraph(ev.get("finding", ""), body_style),
                Paragraph(f"<b>{ev.get('severity', '')}</b>", ParagraphStyle("Sev", fontSize=10, textColor=sev_color))
            ])

        et = Table(table_data, colWidths=[90, 360, 60])
        et.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SURFACE_LIGHT),
            ('TEXTCOLOR', (0,0), (-1,0), TEXT_MAIN),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(et)
    else:
        elements.append(Paragraph("No automated evidence findings available.", body_style))
    
    elements.append(Spacer(1, 20))

    # 4. Detailed Agent Breakdown (Conditional)
    agent_sections = [
        ("Financial Statement Analysis", payload.get("financial_findings")),
        ("Flow of Funds / Graph Analysis", payload.get("graph_findings")),
        ("Compliance & Regulatory Checks", payload.get("compliance_findings")),
        ("Behavioral Audio Analysis", payload.get("audio_findings")),
        ("Media Sentiment & Real-time News", payload.get("news_findings")),
    ]
    for section_title, findings in agent_sections:
        if findings:
            _add_agent_section(elements, styles, header_style, subsection_style, body_style, section_title, findings)

    # Footer
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("-" * 120, footer_style))
    elements.append(Paragraph(
        "CONFIDENTIAL: This document is an AI-generated forensic artifact for demonstration purposes. "
        "SathyaNishta uses multi-agent synthesis to automate deep-market investigations.", footer_style))

    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()

    filename = f"SathyaNishta_Report_{company_name.replace(' ', '_')}.pdf"
    
    _logger.info(f"PDF generated successfully: {filename} ({len(pdf_content)} bytes)")

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition"
        },
    )
