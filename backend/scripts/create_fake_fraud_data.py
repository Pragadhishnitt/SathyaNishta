"""Script to generate fake fraud data for a dummy company.

Run this script inside the docker container to insert:
- Suspicious financial filings
- Deceptive audio transcripts
into Supabase for the company "FraudCorp".

It also prints Neo4j cypher queries to create a circular trading loop.
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import create_engine, text
from sqlmodel import Session

from app.core.config import settings


def insert_fraud_data():
    engine = create_engine(settings.DATABASE_URL)
    company = "FraudCorp"

    financial_content = """
    Q3 2024 Balance Sheet Notes:
    - Related Party Transactions (RPT) surged by 450% compared to previous quarter, routed through offshore shell entities.
    - Cash flows show a negative divergence of ₹4,500 Cr despite reported standalone profits.
    - Unexplained high-value advances given to untraceable vendors.
    """

    audio_content = """
    CEO Earnings Call Q3 2024:
    "We are very confident... uh, mostly confident in our revenue targets. 
    Look, the offshore transactions are totally normal, I don't know why everyone is so focused on them. 
    To be completely honest, I didn't personally authorize those specific transfers. 
    We will, you know, eventually provide full disclosures when the time is right."
    """

    finance_metadata = json.dumps({"is_synthetic": True, "notes": "fake fraud data"})
    audio_trans_metadata = json.dumps({"is_synthetic": True, "notes": "fake fraud data"})

    # Detailed metadata for AudioAgent to detect markers and tone
    audio_file_metadata = {
        "is_synthetic": True,
        "tone_analysis": {
            "overall_tone": "defensive/anxious",
            "confidence": 0.92,
            "segments": [
                {
                    "start": 10,
                    "end": 25,
                    "tone": "hesitant",
                    "transcript": "uh, mostly confident",
                },
                {
                    "start": 45,
                    "end": 60,
                    "tone": "defensive",
                    "transcript": "totally normal... don't know why everyone is so focused",
                },
            ],
        },
        "deception_analysis": {
            "likelihood": 0.85,
            "hedging_count": 4,
            "avoidance_count": 2,
            "explanation": "Significant presence of hedging ('mostly', 'eventually') and defensive topic avoidance regarding offshore transfers.",
            "markers": [
                {"type": "hedging", "text": "mostly confident", "confidence": 0.8},
                {
                    "type": "detachment",
                    "text": "didn't personally authorize",
                    "confidence": 0.9,
                },
            ],
        },
    }

    with Session(engine) as session:
        # 0. Ensure audio_files table exists (since it's missing in Supabase)
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS audio_files (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                company_name VARCHAR(255) NOT NULL,
                call_type VARCHAR(50),
                period VARCHAR(20),
                call_date DATE,
                file_key TEXT NOT NULL,
                duration_sec INT,
                transcript TEXT,
                participants JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            );
        """
            )
        )

        # 1. Insert Financial Data (Vector Search Data)
        session.execute(
            text(
                """
                INSERT INTO financial_filings (id, company_name, company_ticker, period, doc_type, content_chunk, metadata)
                VALUES (:id, :company, :ticker, :period, :doc_type, :content, :meta)
            """
            ),
            {
                "id": str(uuid.uuid4()),
                "company": company,
                "ticker": "FRAUD",
                "period": "Q3-2024",
                "doc_type": "balance_sheet",
                "content": financial_content,
                "meta": finance_metadata,
            },
        )

        # 2. Insert Audio Transcription (Vector Search Data)
        session.execute(
            text(
                """
                INSERT INTO audio_transcriptions (company_name, company_code, transcript_date, content_chunk, chunk_number, metadata)
                VALUES (:company, :code, :date, :content, :chunk, :meta)
            """
            ),
            {
                "company": company,
                "code": "FRAUD",
                "date": datetime.now().date(),
                "content": audio_content,
                "chunk": 1,
                "meta": audio_trans_metadata,
            },
        )

        # 3. Insert Audio File Metadata (Agent Tool Query Data)
        session.execute(
            text(
                """
                INSERT INTO audio_files (company_name, call_type, period, call_date, file_key, duration_sec, transcript, metadata)
                VALUES (:company, :call_type, :period, :date, :file_key, :duration, :transcript, CAST(:meta AS jsonb))
            """
            ),
            {
                "company": company,
                "call_type": "earnings_call",
                "period": "Q3-2024",
                "date": datetime.now().date(),
                "file_key": "synthetic_fraud_call.wav",
                "duration": 120,
                "transcript": audio_content,
                "meta": json.dumps(audio_file_metadata),
            },
        )

        session.commit()

    print(f"✅ Fraud data for {company} inserted into Supabase (Financial + Audio + Tables).")
    print("\n" + "=" * 50)
    print("NEO4J CIRCULAR TRADING SETUP")
    print("=" * 50)
    print("To make the Graph Agent flag FraudCorp, connect to your Neo4j Auradb")
    print("and execute the following Cypher query to create a circular loop:\n")
    print(
        f"""
    CREATE (f:Company {{name: '{company}', cin: 'L12345MH2024PLC123'}}),
           (s1:ShellEntity {{name: 'Obscura Holdings', registration_address: 'Cayman Islands'}}),
           (s2:ShellEntity {{name: 'Mirage Ventures', registration_address: 'BVI'}}),
           
           (f)-[:TRANSACTS_WITH {{amount: 500.0, date: '2024-10-01', description: 'Consulting fees'}}]->(s1),
           (s1)-[:TRANSACTS_WITH {{amount: 495.0, date: '2024-10-02', description: 'Software license'}}]->(s2),
           (s2)-[:TRANSACTS_WITH {{amount: 490.0, date: '2024-10-03', description: 'Equipment advance'}}]->(f)
    """
    )
    print("Once this is run, searching 'Investigate FraudCorp' in SathyaNishta")
    print("will yield a High/Critical Risk scorecard with all agents firing alerts.")


if __name__ == "__main__":
    insert_fraud_data()
