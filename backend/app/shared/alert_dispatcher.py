import os
from datetime import datetime
from typing import List

import httpx

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

VERDICT_EMOJI = {
    "CRITICAL": "🚨",
    "HIGH_RISK": "⚠️",
    "CAUTION": "🟡",
    "SAFE": "✅",
}


async def dispatch_risk_alert(company: str, score: float, verdict: str, top_findings: List[str]) -> None:
    """Send Slack alert for severe verdicts. Failures are non-fatal."""
    if not SLACK_WEBHOOK_URL or verdict not in ("CRITICAL", "HIGH_RISK"):
        return

    emoji = VERDICT_EMOJI.get(verdict, "⚠️")
    findings_text = "\n".join([f"• {f[:120]}" for f in top_findings[:3]])

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} SathyaNishta Alert: {company}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Verdict:*\n{verdict}"},
                    {"type": "mrkdwn", "text": f"*Risk Score:*\n{score}/10"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.now().strftime('%d %b %Y %H:%M IST')}",
                    },
                    {"type": "mrkdwn", "text": "*Platform:*\nSathyaNishta"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Top Findings:*\n{findings_text}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Full Investigation",
                        },
                        "style": "danger",
                        "url": (
                            f"{os.getenv('APP_URL', 'http://127.0.0.1:3000')}/"
                            f"?q=Investigate%20{company.replace(' ', '%20')}"
                        ),
                    }
                ],
            },
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post(SLACK_WEBHOOK_URL, json=payload, timeout=5.0)
        except Exception:
            pass
