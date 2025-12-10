"""
Tests for Dispute RAG Service
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil

from app.services.dispute_service import (
    DisputeService,
    DisputeFilters,
    DisputeResponse,
    DisputeCase,
    DISPUTE_SYSTEM_PROMPT
)
from app.services.vector_store import VectorStore, Document, SearchResult


@pytest.fixture
def temp_index_dir():
    """Create temporary directory for vector store"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_vector_store(temp_index_dir):
    """Create mock vector store with sample documents"""
    store = VectorStore(index_path=temp_index_dir)

    # Add sample dispute documents
    documents = [
        Document(
            id="dispute_001",
            content="áĞáĞÛĞà×ÚİÛ ÒĞÜØîØÚĞ ÓæÒ-á ÓĞÕĞ ÓĞ ÓĞĞÓÒØÜĞ, àİÛ ÒĞÜĞÙÕÔ×Ø ãÜÓĞ Øçİá 18% ÛãîÚØ 166-Øá ÛØîÔÓÕØ×.",
            metadata={
                "case_id": "001",
                "court": "ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ",
                "date": "2023-05-15",
                "cited_articles": ["166"]
            }
        ),
        Document(
            id="dispute_002",
            content="áĞèÔÛİáĞÕÚİ ÒĞÓĞáĞîĞÓØá ÓĞÕĞèØ áĞáĞÛĞà×ÚİÛ ÛîĞàØ ÓĞãíØàĞ ÒĞÓĞáĞîĞÓØá ÒĞÓĞÛîÓÔÚá.",
            metadata={
                "case_id": "002",
                "court": "áĞåĞÚĞåİ áĞáĞÛĞà×Úİ",
                "date": "2023-06-20",
                "cited_articles": ["168"]
            }
        )
    ]

    import asyncio
    asyncio.run(store.add_documents(documents))

    return store


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client"""
    client = Mock()
    client.generate_response = AsyncMock()
    client.generate_response.return_value = "ÓæÒ-á ÒĞÜĞÙÕÔ×Ø ĞàØá 18 ŞàİêÔÜâØ, àİÒİàê Ôá ÒĞÜáĞÖæÕàãÚØĞ ÛãîÚØ 166-Ø×. áĞåÛÔ #001 (2023-05-15) ĞÓĞáâãàÔÑá ĞÛ ÒĞÜĞÙÕÔ×á."
    return client


class TestDisputeFilters:
    """Test DisputeFilters model"""

    def test_filters_creation(self):
        """Test creating dispute filters"""
        filters = DisputeFilters(
            court="ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ",
            date_from=date(2023, 1, 1),
            date_to=date(2023, 12, 31),
            cited_articles=["166", "168"]
        )

        assert filters.court == "ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ"
        assert filters.date_from == date(2023, 1, 1)
        assert filters.date_to == date(2023, 12, 31)
        assert filters.cited_articles == ["166", "168"]

    def test_filters_optional(self):
        """Test filters are optional"""
        filters = DisputeFilters()

        assert filters.court is None
        assert filters.date_from is None
        assert filters.date_to is None
        assert filters.cited_articles is None


class TestDisputeCase:
    """Test DisputeCase model"""

    def test_case_creation(self):
        """Test creating a dispute case"""
        case = DisputeCase(
            case_id="001",
            court="ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ",
            date=date(2023, 5, 15),
            summary="Test summary",
            cited_articles=["166"],
            relevance_score=0.92,
            full_text_available=True
        )

        assert case.case_id == "001"
        assert case.court == "ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ"
        assert case.relevance_score == 0.92


class TestDisputeResponse:
    """Test DisputeResponse model"""

    def test_response_creation(self):
        """Test creating a dispute response"""
        case = DisputeCase(
            case_id="001",
            court="test",
            date=date.today(),
            summary="test",
            cited_articles=[],
            relevance_score=0.9,
            full_text_available=True
        )

        response = DisputeResponse(
            answer="Test answer",
            cases_cited=[case],
            relevant_tax_articles=["166"],
            confidence=0.88,
            model_used="gemini-pro",
            processing_time_ms=1250
        )

        assert response.answer == "Test answer"
        assert len(response.cases_cited) == 1
        assert response.relevant_tax_articles == ["166"]
        assert response.confidence == 0.88


class TestDisputeService:
    """Test DisputeService functionality"""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_vector_store, mock_gemini_client):
        """Test service initialization"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        result = await service.initialize()

        assert result is True
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_initialization_empty_store(self, temp_index_dir, mock_gemini_client):
        """Test initialization with empty vector store"""
        empty_store = VectorStore(index_path=temp_index_dir)
        service = DisputeService(
            vector_store=empty_store,
            gemini_client=mock_gemini_client
        )

        result = await service.initialize()

        # Should still succeed but warn about empty store
        assert result is True

    @pytest.mark.asyncio
    async def test_query_success(self, mock_vector_store, mock_gemini_client):
        """Test successful dispute query"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )
        await service.initialize()

        response = await service.query("àĞ ĞàØá ÓæÒ-á ÒĞÜĞÙÕÔ×Ø?")

        assert isinstance(response, DisputeResponse)
        assert len(response.answer) > 0
        assert response.model_used == "gemini-pro"
        assert response.processing_time_ms > 0
        assert 0 <= response.confidence <= 1

    @pytest.mark.asyncio
    async def test_query_with_filters(self, mock_vector_store, mock_gemini_client):
        """Test query with filters"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )
        await service.initialize()

        filters = DisputeFilters(
            court="ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ",
            date_from=date(2023, 1, 1)
        )

        response = await service.query("ÓæÒ", filters=filters)

        assert isinstance(response, DisputeResponse)
        # Cases should be filtered by court
        for case in response.cases_cited:
            assert case.court == "ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ"

    @pytest.mark.asyncio
    async def test_query_no_results(self, temp_index_dir, mock_gemini_client):
        """Test query with no matching cases"""
        empty_store = VectorStore(index_path=temp_index_dir)
        service = DisputeService(
            vector_store=empty_store,
            gemini_client=mock_gemini_client
        )
        await service.initialize()

        response = await service.query("test query")

        assert response.answer == "ÕÔà ÛİØëÔÑÜĞ àÔÚÔÕĞÜâãàØ áĞåÛÔÔÑØ ×åÕÔÜØ ÙØ×îÕØá×ÕØá."
        assert len(response.cases_cited) == 0
        assert response.confidence == 0.0

    @pytest.mark.asyncio
    async def test_query_llm_failure(self, mock_vector_store):
        """Test query when LLM fails"""
        # Create client that fails
        failing_client = Mock()
        failing_client.generate_response = AsyncMock(side_effect=Exception("API Error"))

        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=failing_client
        )
        await service.initialize()

        response = await service.query("test")

        # Should return error message
        assert "ÕÔà ÛİîÔàîÓĞ" in response.answer
        assert response.model_used == "error"

    @pytest.mark.asyncio
    async def test_get_case_by_id(self, mock_vector_store, mock_gemini_client):
        """Test retrieving case by ID"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )
        await service.initialize()

        case = await service.get_case("001")

        assert case is not None
        assert case.case_id == "001"
        assert case.court == "ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ"
        assert case.relevance_score == 1.0

    @pytest.mark.asyncio
    async def test_get_case_not_found(self, mock_vector_store, mock_gemini_client):
        """Test retrieving non-existent case"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )
        await service.initialize()

        case = await service.get_case("999")

        assert case is None

    def test_get_status(self, mock_vector_store, mock_gemini_client):
        """Test getting service status"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        status = service.get_status()

        assert "initialized" in status
        assert "ready" in status
        assert "total_cases" in status
        assert status["gemini_available"] is True

    def test_extract_tax_articles(self, mock_vector_store, mock_gemini_client):
        """Test extracting tax article numbers from text"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        text = "ÛãîÚØ 166 ÓĞ ÛãîÚØ 168 ÒĞÜáĞÖæÕàĞÕá ÓæÒ-á ìÔáÔÑá. ÛãîÚØ 82.1 ĞáÔÕÔ ÛÜØèÕÜÔÚİÕĞÜØĞ."
        articles = service._extract_tax_articles(text)

        assert "166" in articles
        assert "168" in articles
        # Should handle variations

    def test_calculate_confidence(self, mock_vector_store, mock_gemini_client):
        """Test confidence calculation"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        cases = [
            DisputeCase(
                case_id="1",
                court="test",
                date=date.today(),
                summary="test",
                cited_articles=[],
                relevance_score=0.9,
                full_text_available=True
            ),
            DisputeCase(
                case_id="2",
                court="test",
                date=date.today(),
                summary="test",
                cited_articles=[],
                relevance_score=0.8,
                full_text_available=True
            )
        ]

        confidence = service._calculate_confidence(cases)

        assert 0 <= confidence <= 1
        assert confidence == pytest.approx(0.85, rel=0.01)

    def test_build_context(self, mock_vector_store, mock_gemini_client):
        """Test building context from cases"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        cases = [
            DisputeCase(
                case_id="001",
                court="ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ",
                date=date(2023, 5, 15),
                summary="Test case summary",
                cited_articles=["166"],
                relevance_score=0.9,
                full_text_available=True
            )
        ]

        context = service._build_context(cases)

        assert "áĞåÛÔ #1" in context
        assert "001" in context
        assert "ãÖÔÜĞÔáØ áĞáĞÛĞà×Úİ" in context
        assert "166" in context

    def test_apply_date_filters(self, mock_vector_store, mock_gemini_client):
        """Test applying date filters"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        # Create search results
        doc = Document(
            id="test",
            content="test",
            metadata={"date": "2023-05-15"}
        )
        results = [SearchResult(document=doc, score=0.9, match_type="hybrid")]

        # Filter with date range
        filters = DisputeFilters(
            date_from=date(2023, 1, 1),
            date_to=date(2023, 12, 31)
        )

        filtered = service._apply_filters(results, filters)

        assert len(filtered) == 1

        # Filter that excludes
        filters2 = DisputeFilters(date_from=date(2024, 1, 1))
        filtered2 = service._apply_filters(results, filters2)

        assert len(filtered2) == 0

    def test_apply_article_filters(self, mock_vector_store, mock_gemini_client):
        """Test applying article filters"""
        service = DisputeService(
            vector_store=mock_vector_store,
            gemini_client=mock_gemini_client
        )

        doc = Document(
            id="test",
            content="test",
            metadata={"cited_articles": ["166", "168"]}
        )
        results = [SearchResult(document=doc, score=0.9, match_type="hybrid")]

        # Filter for article 166
        filters = DisputeFilters(cited_articles=["166"])
        filtered = service._apply_filters(results, filters)

        assert len(filtered) == 1

        # Filter for article not in case
        filters2 = DisputeFilters(cited_articles=["999"])
        filtered2 = service._apply_filters(results, filters2)

        assert len(filtered2) == 0


class TestDisputeSystemPrompt:
    """Test dispute system prompt"""

    def test_prompt_format(self):
        """Test system prompt can be formatted"""
        cases = "Test cases"
        question = "Test question"

        prompt = DISPUTE_SYSTEM_PROMPT.format(
            cases=cases,
            question=question
        )

        assert "Test cases" in prompt
        assert "Test question" in prompt
        assert "ÔåáŞÔàâØ" in prompt
