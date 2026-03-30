import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.db import get_session
from ...core.rate_limit import check_rate_limit, email_limiter
from ...core.security import get_current_user
from ...models.user import User

router = APIRouter()

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@sathyanishta.com")


class EmailReportRequest(BaseModel):
    recipients: List[str]
    subject: Optional[str] = None
    message: Optional[str] = None
    investigation_data: dict
    report_type: str = "investigation"  # investigation, brief, compare

    def validate_email(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def get_valid_recipients(self) -> List[str]:
        """Get only valid email addresses"""
        return [email for email in self.recipients if self.validate_email(email)]


def send_investigation_report_email(
    recipients: List[str],
    subject: str,
    message: str,
    investigation_data: dict,
    report_type: str,
):
    """Send investigation report email"""
    if not SMTP_USER or not SMTP_PASSWORD or "your-email" in SMTP_USER:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service not configured. Please set SMTP_USER and SMTP_PASSWORD environment variables.",
        )

    # Generate HTML content based on report type
    if report_type == "investigation":
        html_content = generate_investigation_html(investigation_data, message)
    elif report_type == "brief":
        html_content = generate_brief_html(investigation_data, message)
    elif report_type == "compare":
        html_content = generate_compare_html(investigation_data, message)
    else:
        html_content = generate_default_html(investigation_data, message)

    try:
        for recipient in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = FROM_EMAIL
            msg["To"] = recipient

            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()

    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email",
        )


def generate_investigation_html(data: dict, custom_message: str) -> str:
    """Generate HTML for investigation report"""
    # data is the synthesis payload directly
    evidence = data.get("evidence", [])
    risk_score = data.get("fraud_risk_score", data.get("risk_score", 0))
    company_name = data.get("company_name", "Unknown Company")
    verdict = data.get("verdict", "SAFE")

    risk_color = "#ef4444" if risk_score >= 7.0 else "#f59e0b" if risk_score >= 4.0 else "#10b981"
    risk_level = verdict

    evidence_html = ""
    for item in evidence:  # Show all evidence items
        evidence_html += f"""
        <div style="background: #f8fafc; padding: 12px; margin: 8px 0; border-left: 4px solid #6366f1; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h4 style="margin: 0 0 4px 0; color: #1f2937; font-size: 14px;">{item.get('finding', 'Unknown')}</h4>
            </div>
            <p style="margin: 0; color: #6b7280; font-size: 12px;">Source: {item.get('source', 'Unknown')} | Severity: {item.get('severity', 'N/A')}</p>
        </div>
        """

    summary_html = f"""
    <div class="section">
        <h3 style="color: #1f2937; margin-bottom: 12px;">\U0001F4DD Investigation Verdict</h3>
        <p style="color: #4b5563; line-height: 1.6; font-weight: bold;">
            Based on the multi-agent analysis, the overall verdict for {company_name} is: <span style="background: {risk_color}; color: white; padding: 2px 6px; border-radius: 4px;">{verdict}</span>
        </p>
        <p style="color: #4b5563; line-height: 1.6;">
            The system aggregated findings from financial filings, graph network analysis, compliance checks, and external news/audio data to formulate this score.
        </p>
    </div>
    """

    recommendations_html = ""

    custom_message_html = ""
    if custom_message:
        custom_message_html = f"""
        <div style="background: #f0f9ff; padding: 16px; border-radius: 8px; margin-bottom: 24px; border-left: 4px solid #0ea5e9;">
            <p style="margin: 0;"><strong>Message from sender:</strong> {custom_message}</p>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sathya Nishta Investigation Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #374151; }}
            .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 24px; text-align: center; }}
            .content {{ padding: 24px; max-width: 600px; margin: 0 auto; }}
            .risk-score {{ background: {risk_color}; color: white; padding: 16px; border-radius: 8px; text-align: center; margin: 16px 0; }}
            .risk-number {{ font-size: 36px; font-weight: bold; }}
            .section {{ margin: 24px 0; }}
            .footer {{ background: #f3f4f6; padding: 16px; text-align: center; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">\U0001F50D Forensic Investigation Report</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Sathya Nishta AI-Powered Analysis</p>
        </div>
        
        <div class="content">
            {custom_message_html}
            
            <div class="section">
                <h2 style="color: #1f2937; margin-bottom: 8px;">Company: {company_name}</h2>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="risk-score">
                <div class="risk-number">{risk_score}/100</div>
                <div>{risk_level}</div>
            </div>
            
            <div class="section">
                <h3 style="color: #1f2937; margin-bottom: 12px;">\U0001F50D Key Findings</h3>
                {evidence_html or '<p style="color: #6b7280;">No significant findings detected.</p>'}
            </div>
            
            {summary_html}
            
            {recommendations_html}
        </div>
        
        <div class="footer">
            <p>This report was generated by Sathya Nishta, an AI-powered forensic investigation platform.</p>
            <p>For questions or additional analysis, please contact the investigation team.</p>
        </div>
    </body>
    </html>
    """


def generate_brief_html(data: dict, custom_message: str) -> str:
    """Generate HTML for market brief"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sathya Nishta Market Brief</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #374151; }}
            .header {{ background: linear-gradient(135deg, #10b981, #06b6d4); color: white; padding: 24px; text-align: center; }}
            .content {{ padding: 24px; max-width: 600px; margin: 0 auto; }}
            .footer {{ background: #f3f4f6; padding: 16px; text-align: center; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">\U0001F4CA Market Intelligence Brief</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Sathya Nishta AI Analysis</p>
        </div>
        
        <div class="content">
            {custom_message and f'<div style="background: #f0f9ff; padding: 16px; border-radius: 8px; margin-bottom: 24px; border-left: 4px solid #0ea5e9;"><p style="margin: 0;"><strong>Message from sender:</strong> {custom_message}</p></div>'}
            
            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <pre style="margin: 0; font-family: monospace; font-size: 12px; white-space: pre-wrap;">{str(data)}</pre>
            </div>
        </div>
        
        <div class="footer">
            <p>This brief was generated by Sathya Nishta AI-powered market intelligence platform.</p>
        </div>
    </body>
    </html>
    """


def generate_compare_html(data: dict, custom_message: str) -> str:
    """Generate HTML for comparison report"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sathya Nishta Comparison Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #374151; }}
            .header {{ background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; padding: 24px; text-align: center; }}
            .content {{ padding: 24px; max-width: 600px; margin: 0 auto; }}
            .footer {{ background: #f3f4f6; padding: 16px; text-align: center; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">\u2696\ufe0f Comparison Analysis Report</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Sathya Nishta AI Comparison</p>
        </div>
        
        <div class="content">
            {custom_message and f'<div style="background: #f0f9ff; padding: 16px; border-radius: 8px; margin-bottom: 24px; border-left: 4px solid #0ea5e9;"><p style="margin: 0;"><strong>Message from sender:</strong> {custom_message}</p></div>'}
            
            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <pre style="margin: 0; font-family: monospace; font-size: 12px; white-space: pre-wrap;">{str(data)}</pre>
            </div>
        </div>
        
        <div class="footer">
            <p>This comparison was generated by Sathya Nishta AI-powered analysis platform.</p>
        </div>
    </body>
    </html>
    """


def generate_default_html(data: dict, custom_message: str) -> str:
    """Generate default HTML for other report types"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sathya Nishta Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #374151; }}
            .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 24px; text-align: center; }}
            .content {{ padding: 24px; max-width: 600px; margin: 0 auto; }}
            .footer {{ background: #f3f4f6; padding: 16px; text-align: center; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">\U0001F4C4 Sathya Nishta Report</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">AI-Powered Analysis</p>
        </div>
        
        <div class="content">
            {custom_message and f'<div style="background: #f0f9ff; padding: 16px; border-radius: 8px; margin-bottom: 24px; border-left: 4px solid #0ea5e9;"><p style="margin: 0;"><strong>Message from sender:</strong> {custom_message}</p></div>'}
            
            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <pre style="margin: 0; font-family: monospace; font-size: 12px; white-space: pre-wrap;">{str(data)}</pre>
            </div>
        </div>
        
        <div class="footer">
            <p>This report was generated by Sathya Nishta AI-powered analysis platform.</p>
        </div>
    </body>
    </html>
    """


@router.post("/send-report")
async def send_report_email(request: EmailReportRequest, http_request: Request = None):
    """Send investigation report via email"""
    # Rate limit by client IP instead of user email (auth removed for demo)
    client_ip = http_request.client.host if http_request and http_request.client else "unknown"
    check_rate_limit(email_limiter, client_ip, "Too many email requests. Please try again later.")

    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one recipient is required",
        )

    # Validate and filter recipients
    valid_recipients = request.get_valid_recipients()
    if len(valid_recipients) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid email addresses provided",
        )

    if len(valid_recipients) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 recipients allowed",
        )

    # Generate subject if not provided
    subject = request.subject or "Sathya Nishta Investigation Report"

    try:
        send_investigation_report_email(
            recipients=valid_recipients,
            subject=subject,
            message=request.message or "",
            investigation_data=request.investigation_data,
            report_type=request.report_type,
        )

        return {
            "message": f"Report successfully sent to {len(valid_recipients)} recipient(s)",
            "recipients": valid_recipients,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email. Please try again later.",
        )
