"""
Shared pytest fixtures and configuration for tests

This module provides fixtures for:
- FastAPI test client with async support
- Mocked LLM clients (Gemini, Claude)
- Mocked services (Tax, Dispute, Document)
- Environment configuration for local and cloud testing
- Sample data fixtures
"""

import os
import sys

# ===========================================================================
# CRITICAL: Set environment variables BEFORE any app imports
# This must happen at module load time, not in a fixture
# ===========================================================================
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key-for-testing")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-claude-key-for-testing")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "100")
os.environ.setdefault("RATE_LIMIT_WINDOW", "60")

import pytest
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ===========================================================================
# Environment Setup for Testing
# ===========================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run"""
    # Set required environment variables for testing
    os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key-for-testing")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-claude-key-for-testing")
    os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
    os.environ.setdefault("API_ENV", "dev")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    os.environ.setdefault("RATE_LIMIT_REQUESTS", "100")
    os.environ.setdefault("RATE_LIMIT_WINDOW", "60")

    yield

    # Cleanup can be added here if needed


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration shared across all tests"""
    return {
        "api_url": "http://localhost:8000",
        "timeout": 30,
        "test_conversation_id": "test-conversation-123",
        "admin_api_key": "test-admin-key",
        "test_user_id": "test-user-456",
        "max_retries": 3,
        "retry_delay": 0.1,  # Fast retries for tests
    }


# ===========================================================================
# Event Loop Configuration
# ===========================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ===========================================================================
# FastAPI Test Client Fixtures
# ===========================================================================

@pytest.fixture
def mock_services():
    """Create mock services to avoid real initialization"""
    mock_tax = Mock()
    mock_tax.initialize = AsyncMock(return_value=True)
    mock_tax.get_tax_answer = AsyncMock(return_value={
        "answer": "Mock tax answer",
        "sources": []
    })
    mock_tax.get_status = Mock(return_value={"ready": True, "initialized": True})

    mock_dispute = Mock()
    mock_dispute.initialize = AsyncMock(return_value=True)
    mock_dispute.query = AsyncMock(return_value=Mock(
        answer="Mock dispute answer",
        cases=[]
    ))
    mock_dispute.get_status = Mock(return_value={"ready": True, "initialized": True})

    mock_document = Mock()
    mock_document.initialize = AsyncMock(return_value=True)
    mock_document.get_status = Mock(return_value={"ready": True, "initialized": True})

    return {
        "tax_service": mock_tax,
        "dispute_service": mock_dispute,
        "document_service": mock_document,
    }


@pytest.fixture
def client(mock_services):
    """Create synchronous test client with mocked services"""
    with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
         patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
         patch('app.main.DocumentService', return_value=mock_services["document_service"]):
        from app.main import app
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
async def async_client(mock_services):
    """Create async test client for async endpoint testing"""
    with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
         patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
         patch('app.main.DocumentService', return_value=mock_services["document_service"]):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def api_client():
    """Alternative FastAPI test client (for backward compatibility)"""
    # Mock the services during import
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch('app.services.TaxCodeService') as mock_tax, \
             patch('app.services.DisputeService') as mock_dispute, \
             patch('app.services.DocumentService') as mock_doc:
            mock_tax.return_value.initialize = AsyncMock()
            mock_dispute.return_value.initialize = AsyncMock()
            mock_doc.return_value.initialize = AsyncMock()
            from app.main import app
            return TestClient(app)


# ===========================================================================
# LLM Client Mocks
# ===========================================================================

@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client"""
    client = Mock()
    client.generate_response = AsyncMock()
    client.generate_response.return_value = "Mock response from Gemini with მუხლი 166 reference"
    client.upload_file = AsyncMock(return_value=Mock(uri="mock://file-uri"))
    client.count_tokens = Mock(return_value=100)
    return client


@pytest.fixture
def mock_claude_client():
    """Mock Claude API client"""
    client = Mock()
    client.generate_response = AsyncMock()
    client.generate_response.return_value = "Mock response from Claude"
    client.messages = Mock()
    client.messages.create = AsyncMock(return_value=Mock(
        content=[Mock(text="Mock Claude response")]
    ))
    return client


@pytest.fixture
def mock_llm_response_with_citations():
    """Mock LLM response containing Georgian tax code citations"""
    return """
    საგადასახადო კოდექსის თანახმად, დღგ-ს სტანდარტული განაკვეთი არის 18%.

    ეს განისაზღვრება მუხლი 166-ით, რომელიც ადგენს დღგ-ს ძირითად განაკვეთს.

    გარდა ამისა, მუხლი 165 განსაზღვრავს დღგ-ს გადამხდელად რეგისტრაციის წესებს,
    ხოლო მუხლი 167 აწესრიგებს გადახდის ვადებს.

    საშემოსავლო გადასახადის შესახებ იხილეთ მუხლი 168.
    """


# ===========================================================================
# Service Mocks
# ===========================================================================

@pytest.fixture
def mock_tax_service():
    """Mock TaxCodeService"""
    service = Mock()
    service.initialize = AsyncMock(return_value=True)
    service._initialized = True
    service.get_tax_answer = AsyncMock()
    service.get_tax_answer.return_value = {
        "answer": "დღგ-ს სტანდარტული განაკვეთი არის 18%.",
        "sources": [
            {
                "article": "166",
                "title": "დღგ-ს განაკვეთი",
                "content": "დღგ-ს სტანდარტული განაკვეთი არის 18 პროცენტი",
                "matsne_url": "https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_166"
            }
        ],
        "confidence": 0.95,
        "model_used": "gemini-pro"
    }
    service.get_status = Mock(return_value={
        "ready": True,
        "initialized": True,
        "documents_loaded": 1,
        "cache_size": 0
    })
    return service


@pytest.fixture
def mock_dispute_service():
    """Mock DisputeService"""
    service = Mock()
    service.initialize = AsyncMock(return_value=True)
    service._initialized = True
    service.query = AsyncMock()
    service.query.return_value = Mock(
        answer="საბჭოს გადაწყვეტილება დღგ-ის ჩათვლის შესახებ",
        cases_cited=[
            Mock(
                case_id="ТД-2023-100",
                court="დავების საბჭო",
                date="2023-05-15",
                summary="დღგ-ის ჩათვლის უფლება",
                cited_articles=["166"],
                relevance_score=0.92
            )
        ],
        relevant_tax_articles=["166"],
        confidence=0.88,
        model_used="gemini-pro",
        processing_time_ms=1250
    )
    service.get_status = Mock(return_value={
        "ready": True,
        "initialized": True,
        "total_cases": 100,
        "gemini_available": True
    })
    return service


@pytest.fixture
def mock_document_service():
    """Mock DocumentService"""
    service = Mock()
    service.initialize = AsyncMock(return_value=True)
    service._initialized = True
    service.list_document_types = AsyncMock(return_value=[
        Mock(id="nda", name_ka="NDA", name_en="Non-Disclosure Agreement"),
        Mock(id="employment", name_ka="შრომის ხელშეკრულება", name_en="Employment Contract"),
    ])
    service.generate_document = AsyncMock(return_value=Mock(
        document_id="doc-123",
        document_type="nda",
        content="# Generated Document\n\nContent here...",
        format="markdown",
        created_at=datetime.utcnow(),
        warnings=[]
    ))
    service.get_status = Mock(return_value={
        "ready": True,
        "initialized": True,
        "templates_loaded": 6
    })
    return service


@pytest.fixture
def mock_orchestrator(mock_tax_service, mock_dispute_service):
    """Mock Orchestrator"""
    from app.models import QueryMode, UnifiedResponse, ResponseSources, CitedArticle

    orchestrator = Mock()
    orchestrator.tax_service = mock_tax_service
    orchestrator.dispute_service = mock_dispute_service

    orchestrator.auto_classify = AsyncMock(return_value=QueryMode.TAX)
    orchestrator.route_query = AsyncMock(return_value=UnifiedResponse(
        answer="Mock unified response",
        mode_used=QueryMode.TAX,
        sources=ResponseSources(
            tax_articles=[
                CitedArticle(
                    article_number="166",
                    title="დღგ-ს განაკვეთი",
                    snippet="18%"
                )
            ],
            cases=[],
            templates=[]
        ),
        citations_verified=True,
        warnings=[],
        processing_time_ms=500
    ))
    orchestrator.get_status = Mock(return_value={
        "tax_service": {"ready": True},
        "dispute_service": {"ready": True}
    })

    return orchestrator


# ===========================================================================
# Sample Data Fixtures
# ===========================================================================

@pytest.fixture
def sample_tax_response():
    """Sample tax code response with citations"""
    return {
        "answer": """
        დღგ-ს სტანდარტული განაკვეთი არის 18 პროცენტი.
        ეს განისაზღვრება საგადასახადო კოდექსის მუხლი 166-ით.
        დღგ-ს გადამხდელად რეგისტრაცია მუხლი 165-ით არეგულირება.
        """,
        "sources": [
            {
                "article": "166",
                "title": "დღგ-ს განაკვეთი",
                "content": "დღგ-ს სტანდარტული განაკვეთი არის 18 პროცენტი",
                "matsne_url": "https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_166"
            },
            {
                "article": "165",
                "title": "დღგ-ს გადამხდელი",
                "content": "გადამხდელად რეგისტრაცია სავალდებულოა, როდესაც ბრუნვა აღემატება 100,000 ლარს",
                "matsne_url": "https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_165"
            }
        ],
        "confidence": 0.95,
        "model_used": "gemini-pro"
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request payload"""
    return {
        "message": "რა არის დღგ-ს სტანდარტული განაკვეთი?",
        "conversation_id": "test-123",
        "mode": "tax",
        "language": "ka"
    }


@pytest.fixture
def sample_document_request():
    """Sample document generation request"""
    return {
        "document_type": "nda",
        "template_id": "nda_standard_ka",
        "variables": {
            "party_a_name": "შპს ტესტი",
            "party_b_name": "შპს მეორე",
            "effective_date": "2024-01-01",
            "confidential_info": "საქმიანი ინფორმაცია",
            "duration_months": 12
        },
        "language": "ka",
        "format": "markdown"
    }


@pytest.fixture
def sample_dispute_cases():
    """Sample dispute cases for testing"""
    return [
        {
            "doc_number": "ТД-2023-100",
            "date": "2023-05-15",
            "category": "დღგ",
            "decision_type": "satisfied",
            "snippet": "საბჭომ დაკმაყოფილდა საჩივარი დღგ-ის ჩათვლის უფლების შესახებ"
        },
        {
            "doc_number": "ТД-2023-101",
            "date": "2023-06-20",
            "category": "საშემოსავლო",
            "decision_type": "rejected",
            "snippet": "საშემოსავლო გადასახადის დარიცხვა სწორად განხორციელდა"
        },
        {
            "doc_number": "ТД-2023-102",
            "date": "2023-07-10",
            "category": "მოგება",
            "decision_type": "partially_satisfied",
            "snippet": "ნაწილობრივ დაკმაყოფილდა საჩივარი მოგების გადასახადის შესახებ"
        }
    ]


# ===========================================================================
# Cleanup and Reset Fixtures
# ===========================================================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test"""
    yield
    # Cleanup happens here if needed


@pytest.fixture
def clean_conversation_store():
    """Provide a clean conversation store for tests"""
    from app.storage.conversation_store import ConversationStore
    store = ConversationStore(max_conversations=100, ttl_hours=24)
    yield store
    # Clear all conversations after test
    store._conversations.clear()


# ===========================================================================
# Pytest Configuration
# ===========================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "cloud: mark test as cloud deployment test")
    config.addinivalue_line("markers", "smoke: mark test as smoke test for quick verification")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests by default"""
    if not config.getoption("--run-integration", default=False):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

    if not config.getoption("--run-slow", default=False):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-cloud",
        action="store_true",
        default=False,
        help="run cloud deployment tests"
    )


# ===========================================================================
# Cloud-Ready Test Helpers
# ===========================================================================

@pytest.fixture
def cloud_config():
    """Configuration for cloud deployment testing"""
    return {
        "health_endpoint": "/health",
        "status_endpoint": "/v1/status",
        "startup_timeout_seconds": 30,
        "health_check_interval_seconds": 5,
        "expected_memory_mb": 2048,
        "expected_cpu_cores": 2,
        "expected_env": "prod",
    }


@pytest.fixture
def mock_cloud_env():
    """Mock cloud environment variables"""
    cloud_env = {
        "API_ENV": "prod",
        "LOG_LEVEL": "INFO",
        "PORT": "8080",  # Cloud Run default
        "K_SERVICE": "legal-ai-backend",  # Cloud Run service name
        "K_REVISION": "legal-ai-backend-00001-abc",  # Cloud Run revision
        "K_CONFIGURATION": "legal-ai-backend",  # Cloud Run config
        "GEMINI_API_KEY": "test-gemini-key",
        "ADMIN_API_KEY": "test-admin-key",
    }

    with patch.dict(os.environ, cloud_env):
        yield cloud_env
