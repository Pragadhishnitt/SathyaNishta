from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings
from app.models.user import User
from app.models.chat import ChatThread, ChatMessage
from app.models.data_sources import FinancialFiling, NewsArticle, ComplianceRecord, AudioTranscript

# For Alembic, we might need direct connection
engine = create_engine(settings.DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
