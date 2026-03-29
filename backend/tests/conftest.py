"""
backend/tests/conftest.py

Patches all external service clients (DB, Supabase, Neo4j) before any test
module is imported. This means Settings() can instantiate with dummy env vars
(set in ci.yaml) without any real connection being attempted.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Session-scoped patches — active for the entire pytest run
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def mock_database(session_mocker=None):
    """Prevent any real SQLAlchemy/asyncpg connection attempts."""
    with patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=MagicMock()), \
         patch("sqlalchemy.ext.asyncio.AsyncSession", return_value=AsyncMock()):
        yield


@pytest.fixture(autouse=True, scope="session")
def mock_supabase():
    """Prevent real Supabase client initialisation."""
    with patch("supabase.create_client", return_value=MagicMock()):
        yield


@pytest.fixture(autouse=True, scope="session")
def mock_neo4j():
    """Prevent real Neo4j driver connection."""
    with patch("neo4j.GraphDatabase.driver", return_value=MagicMock()):
        yield


# ---------------------------------------------------------------------------
# Convenience fixtures for individual tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_settings(monkeypatch):
    """
    Override specific settings values inside a single test.
    Usage:
        def test_something(mock_settings):
            mock_settings("DATABASE_URL", "sqlite:///test.db")
    """
    def _set(key, value):
        monkeypatch.setenv(key, value)
    return _set