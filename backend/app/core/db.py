from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.models.chat import ChatMessage, ChatThread
from app.models.data_sources import AudioTranscript, ComplianceRecord, FinancialFiling, NewsArticle
from app.models.user import User

# For Alembic, we might need direct connection
engine = create_engine(settings.DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
