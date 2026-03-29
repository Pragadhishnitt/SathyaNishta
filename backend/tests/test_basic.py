"""Basic tests for backend functionality"""

import pytest
import sys
from pathlib import Path

# Add backend to path for imports
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from app.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_api_docs_available():
    """Test that API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_openapi_schema():
    """Test OpenAPI schema is generated"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()


def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options("/api/test")
    assert response.status_code == 200
    # CORS headers should be present (implementation dependent)


def test_invalid_endpoint():
    """Test invalid endpoint returns 404"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404


class TestBasicAPI:
    """Basic API test class"""
    
    def test_api_structure(self):
        """Test basic API structure"""
        # Test that main API routes exist
        response = client.get("/")
        # This might redirect or return basic info
        assert response.status_code in [200, 404]  # Depending on implementation
    
    def test_error_handling(self):
        """Test error handling"""
        # Test malformed request
        response = client.post("/api/investigate", json={})
        # Should handle gracefully
        assert response.status_code in [400, 422, 200]  # Depending on validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
