import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlmodel import Session

# Ensure the app context is loaded
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
from app.models.data_sources import AudioTranscript
from sqlmodel import Session, SQLModel, create_engine

engine = create_engine(settings.DATABASE_URL)

from datetime import datetime

TRANSCRIPTS = [
    {
        "company": "Adani Enterprises Limited",
        "speaker": "Company Spokesperson",
        "title": "Adani Enterprises Q2 2024 Earnings Call",
        "content": "Good morning. We believe our transactions were at arm's length. The specific details of the Middle East subsidiaries are matters we consider fully compliant. Our legal team will address separately any inquiries regarding Apex Trading.",
        "date": datetime.now()
    },
    {
        "company": "Reliance Industries Limited",
        "speaker": "Executive Board",
        "title": "Reliance AGM 2024 Transcripts",
        "content": "We have seen robust growth across all sectors. In response to the analyst question regarding the Kotak and Birla capital returns, our structured financing mechanisms are entirely standard and there are absolutely no irregularities whatsoever in our subsidiary relationships.",
        "date": datetime.now()
    },
    {
        "company": "Tata Consultancy Services",
        "speaker": "CFO",
        "title": "TCS Q3 2024 Earnings Call",
        "content": "Our IT outsourcing contracts with UAE entities remain stable. Regarding the tech license fee from Mauritius, we maintain transparency. There is no truth to the rumors of shell entity routing.",
        "date": datetime.now()
    }
]

def seed_audio_data():
    print("Database URL:", settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Check if we already have data
        count = session.query(AudioTranscript).count()
        if count > 0:
            print(f"Skipping audio seed. {count} transcripts already exist.")
            return

        print("Seeding audio transcripts...")
        for data in TRANSCRIPTS:
            transcript = AudioTranscript(
                company=data["company"],
                speaker=data["speaker"],
                title=data["title"],
                content=data["content"],
                date=data["date"]
            )
            session.add(transcript)
        
        session.commit()
        print("Successfully seeded audio transcripts.")

if __name__ == "__main__":
    seed_audio_data()
