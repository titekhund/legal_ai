"""
Shared pytest fixtures and configuration for tests
"""

import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "api_url": "http://localhost:8000",
        "timeout": 30,
        "test_conversation_id": "test-conversation-123"
    }


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client"""
    client = Mock()
    client.generate_response = AsyncMock()
    client.generate_response.return_value = "Mock response from Gemini"
    return client


@pytest.fixture
def mock_claude_client():
    """Mock Claude API client"""
    client = Mock()
    client.generate_response = AsyncMock()
    client.generate_response.return_value = "Mock response from Claude"
    return client


@pytest.fixture
def mock_tax_service():
    """Mock TaxCodeService"""
    service = Mock()
    service.get_tax_answer = AsyncMock()
    service.get_tax_answer.return_value = {
        "answer": "Mock tax answer",
        "sources": [
            {
                "article": "166",
                "title": "Mock Article",
                "content": "Mock article content",
                "matsne_url": "https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_166"
            }
        ]
    }
    return service


@pytest.fixture
def sample_tax_response():
    """Sample tax code response with citations"""
    return {
        "answer": """
        гцв-с вамайедзи сахарзедкнши арис 18 орнъдмти.
        дс вамисажцердба савагасаюагн йнгдхсис луюки 166-из.
        гцв-с рдвистраъиа саеакгдбукна луюки 165-ис лиюдгеиз.
        """,
        "sources": [
            {
                "article": "166",
                "title": "гцв-с вамайедзи",
                "content": "гцв-с вамайедзи арис 18 орнъдмти",
                "matsne_url": "https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_166"
            },
            {
                "article": "165",
                "title": "гцв-с рдвистраъиа",
                "content": "рдвистраъиас дхедлгдбардба оири, рнлкис шдлнсаеаки ацдлатдба 100,000 карс",
                "matsne_url": "https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_165"
            }
        ]
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request payload"""
    return {
        "message": "ра арис гцв-с вамайедзи сахарзедкнши?",
        "conversation_id": "test-123"
    }


@pytest.fixture
def api_client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test"""
    yield
    # Cleanup happens here if needed


# Markers for test organization
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "asyncio: mark test as async")


# Skip integration tests by default unless explicitly requested
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests by default"""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
