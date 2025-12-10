"""
Tests for Orchestrator Service
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import date

from app.services.orchestrator import Orchestrator
from app.models import (
    QueryMode,
    UnifiedResponse,
    ResponseSources,
    CitedArticle,
    DisputeCase,
)


class TestAutoClassification:
    """Test automatic mode classification"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mock services"""
        return Orchestrator(
            tax_service=Mock(),
            dispute_service=Mock()
        )

    @pytest.mark.asyncio
    async def test_classify_tax_keywords(self, orchestrator):
        """Test classification with tax-specific keywords"""
        queries = [
            "რა არის დღგ-ს განაკვეთი საქართველოში?",
            "მუხლი 166 რას განსაზღვრავს?",
            "საგადასახადო კოდექსი საშემოსავლო გადასახადის შესახებ",
            "მოგების გადასახადის განაკვეთი რა არის?",
        ]

        for query in queries:
            mode = await orchestrator.auto_classify(query)
            assert mode == QueryMode.TAX, f"Failed to classify as TAX: {query}"

    @pytest.mark.asyncio
    async def test_classify_dispute_keywords(self, orchestrator):
        """Test classification with dispute-specific keywords"""
        queries = [
            "დოკუმენტის # ТД-2023-100 შესახებ",
            "დავების საბჭოს გადაწყვეტილება",
            "ფინანსთა სამინისტროს დავის გადაწყვეტილება",
            "საჩივარი დავის საგნის შესახებ",
            "სადავო საკითხი დარიცხული თანხის შესახებ",
            "გასაჩივრებული გადაწყვეტილება და საბჭოს დასკვნა",
        ]

        for query in queries:
            mode = await orchestrator.auto_classify(query)
            assert mode == QueryMode.DISPUTE, f"Failed to classify as DISPUTE: {query}"

    @pytest.mark.asyncio
    async def test_classify_document_keywords(self, orchestrator):
        """Test classification with document-specific keywords"""
        queries = [
            "ხელშეკრულების შაბლონი",
            "დოკუმენტის ნიმუში",
            "შაბლონი საგადასახადო დეკლარაციისთვის",
        ]

        for query in queries:
            mode = await orchestrator.auto_classify(query)
            assert mode == QueryMode.DOCUMENT, f"Failed to classify as DOCUMENT: {query}"

    @pytest.mark.asyncio
    async def test_classify_mixed_keywords_dispute_priority(self, orchestrator):
        """Test that dispute has priority when matched with tax keywords"""
        query = "დავის საგანი დღგ-ს განაკვეთის შესახებ მუხლი 166"
        # Contains both dispute ("დავის საგანი") and tax ("დღგ", "მუხლი") keywords
        mode = await orchestrator.auto_classify(query)
        # Should be classified as DISPUTE due to priority
        assert mode == QueryMode.DISPUTE

    @pytest.mark.asyncio
    async def test_classify_no_keywords_defaults_tax(self, orchestrator):
        """Test that queries with no keywords default to TAX"""
        queries = [
            "გამარჯობა",
            "რას ნიშნავს ეს?",
            "დამეხმარე გაგებაში",
        ]

        for query in queries:
            mode = await orchestrator.auto_classify(query)
            assert mode == QueryMode.TAX, f"Failed to default to TAX: {query}"


class TestModeRouting:
    """Test query routing to appropriate services"""

    @pytest.fixture
    def mock_tax_service(self):
        """Create mock tax service"""
        service = Mock()
        service.query = AsyncMock()

        # Mock tax response
        mock_response = Mock()
        mock_response.answer = "დღგ-ს განაკვეთი არის 18%"
        mock_response.cited_articles = [
            Mock(
                article_number="166",
                title="დღგ-ს განაკვეთი",
                snippet="დღგ-ს განაკვეთი არის 18 პროცენტი"
            )
        ]
        service.query.return_value = mock_response

        return service

    @pytest.fixture
    def mock_dispute_service(self):
        """Create mock dispute service"""
        service = Mock()
        service.query = AsyncMock()

        # Mock dispute response
        mock_response = Mock()
        mock_response.answer = "საბჭოს გადაწყვეტილება დღგ-ის ჩათვლის შესახებ"
        mock_response.cases = [
            {
                "doc_number": "ТД-2023-100",
                "date": "2023-05-15",
                "category": "დღგ",
                "decision_type": "satisfied",
                "text": "საბჭომ დაკმაყოფილდა საჩივარი დღგ-ის ჩათვლის უფლების შესახებ"
            }
        ]
        service.query.return_value = mock_response

        return service

    @pytest.mark.asyncio
    async def test_route_to_tax(self, mock_tax_service, mock_dispute_service):
        """Test routing to tax service"""
        orchestrator = Orchestrator(
            tax_service=mock_tax_service,
            dispute_service=mock_dispute_service
        )

        response = await orchestrator.route_query(
            message="რა არის დღგ-ს განაკვეთი?",
            mode=QueryMode.TAX
        )

        assert isinstance(response, UnifiedResponse)
        assert response.mode_used == QueryMode.TAX
        assert "18%" in response.answer
        assert len(response.sources.tax_articles) > 0
        assert len(response.sources.cases) == 0
        assert mock_tax_service.query.called

    @pytest.mark.asyncio
    async def test_route_to_dispute(self, mock_tax_service, mock_dispute_service):
        """Test routing to dispute service"""
        orchestrator = Orchestrator(
            tax_service=mock_tax_service,
            dispute_service=mock_dispute_service
        )

        response = await orchestrator.route_query(
            message="დოკუმენტის # ТД-2023-100 შესახებ",
            mode=QueryMode.DISPUTE
        )

        assert isinstance(response, UnifiedResponse)
        assert response.mode_used == QueryMode.DISPUTE
        assert "საბჭოს გადაწყვეტილება" in response.answer
        assert len(response.sources.cases) > 0
        assert len(response.sources.tax_articles) == 0
        assert mock_dispute_service.query.called

    @pytest.mark.asyncio
    async def test_route_auto_classifies(self, mock_tax_service, mock_dispute_service):
        """Test AUTO mode triggers classification"""
        orchestrator = Orchestrator(
            tax_service=mock_tax_service,
            dispute_service=mock_dispute_service
        )

        # Query with clear tax keywords
        response = await orchestrator.route_query(
            message="მუხლი 166 რას განსაზღვრავს?",
            mode=QueryMode.AUTO
        )

        assert response.mode_used == QueryMode.TAX
        assert mock_tax_service.query.called

        # Query with clear dispute keywords
        mock_tax_service.query.reset_mock()
        response = await orchestrator.route_query(
            message="დავის საგანი დღგ-ის ჩათვლის შესახებ",
            mode=QueryMode.AUTO
        )

        assert response.mode_used == QueryMode.DISPUTE
        assert mock_dispute_service.query.called

    @pytest.mark.asyncio
    async def test_route_document_not_implemented(self, mock_tax_service):
        """Test DOCUMENT mode raises not implemented error"""
        orchestrator = Orchestrator(tax_service=mock_tax_service)

        with pytest.raises(ValueError, match="not yet implemented"):
            await orchestrator.route_query(
                message="დოკუმენტის შაბლონი",
                mode=QueryMode.DOCUMENT
            )

    @pytest.mark.asyncio
    async def test_route_missing_service(self):
        """Test routing without required service raises error"""
        orchestrator = Orchestrator(tax_service=None)

        with pytest.raises(ValueError, match="not available"):
            await orchestrator.route_query(
                message="test",
                mode=QueryMode.TAX
            )


class TestUnifiedResponse:
    """Test unified response format"""

    @pytest.fixture
    def mock_tax_service(self):
        """Create mock tax service"""
        service = Mock()
        service.query = AsyncMock()

        # Mock response with multiple citations
        mock_response = Mock()
        mock_response.answer = "Test answer"
        mock_response.cited_articles = [
            Mock(article_number="166", title="Title 1", snippet="Snippet 1"),
            Mock(article_number="168", title="Title 2", snippet="Snippet 2"),
        ]
        service.query.return_value = mock_response

        return service

    @pytest.mark.asyncio
    async def test_response_structure(self, mock_tax_service):
        """Test unified response has correct structure"""
        orchestrator = Orchestrator(tax_service=mock_tax_service)

        response = await orchestrator.route_query(
            message="test question",
            mode=QueryMode.TAX
        )

        # Verify response structure
        assert isinstance(response, UnifiedResponse)
        assert hasattr(response, 'answer')
        assert hasattr(response, 'mode_used')
        assert hasattr(response, 'sources')
        assert hasattr(response, 'citations_verified')
        assert hasattr(response, 'warnings')
        assert hasattr(response, 'processing_time_ms')

        # Verify types
        assert isinstance(response.answer, str)
        assert isinstance(response.mode_used, QueryMode)
        assert isinstance(response.sources, ResponseSources)
        assert isinstance(response.citations_verified, bool)
        assert isinstance(response.warnings, list)
        assert isinstance(response.processing_time_ms, int)

    @pytest.mark.asyncio
    async def test_response_sources_structure(self, mock_tax_service):
        """Test response sources have correct structure"""
        orchestrator = Orchestrator(tax_service=mock_tax_service)

        response = await orchestrator.route_query(
            message="test",
            mode=QueryMode.TAX
        )

        sources = response.sources
        assert hasattr(sources, 'tax_articles')
        assert hasattr(sources, 'cases')
        assert hasattr(sources, 'templates')

        assert isinstance(sources.tax_articles, list)
        assert isinstance(sources.cases, list)
        assert isinstance(sources.templates, list)

        # Verify article structure
        for article in sources.tax_articles:
            assert isinstance(article, CitedArticle)
            assert hasattr(article, 'article_number')
            assert hasattr(article, 'title')
            assert hasattr(article, 'snippet')

    @pytest.mark.asyncio
    async def test_processing_time_recorded(self, mock_tax_service):
        """Test that processing time is recorded"""
        orchestrator = Orchestrator(tax_service=mock_tax_service)

        response = await orchestrator.route_query(
            message="test",
            mode=QueryMode.TAX
        )

        # Processing time should be positive
        assert response.processing_time_ms > 0
        assert response.processing_time_ms < 10000  # Should be under 10 seconds

    @pytest.mark.asyncio
    async def test_citations_verified_flag(self, mock_tax_service):
        """Test citations_verified flag is set correctly"""
        orchestrator = Orchestrator(tax_service=mock_tax_service)

        response = await orchestrator.route_query(
            message="test",
            mode=QueryMode.TAX
        )

        # Should be True when citations are present
        assert response.citations_verified is True

        # Test with no citations
        mock_tax_service.query.return_value.cited_articles = []
        response = await orchestrator.route_query(
            message="test",
            mode=QueryMode.TAX
        )

        assert response.citations_verified is False


class TestServiceStatus:
    """Test service status checks"""

    def test_get_status(self):
        """Test status aggregation"""
        mock_tax = Mock()
        mock_tax.get_status = Mock(return_value={"ready": True, "documents": 100})

        mock_dispute = Mock()
        mock_dispute.get_status = Mock(return_value={"ready": True, "cases": 50})

        orchestrator = Orchestrator(
            tax_service=mock_tax,
            dispute_service=mock_dispute
        )

        status = orchestrator.get_status()

        assert isinstance(status, dict)
        assert "tax_service" in status
        assert "dispute_service" in status
        assert status["tax_service"]["ready"] is True
        assert status["dispute_service"]["ready"] is True

    def test_get_status_missing_services(self):
        """Test status with missing services"""
        orchestrator = Orchestrator(tax_service=None, dispute_service=None)

        status = orchestrator.get_status()

        assert status["tax_service"]["available"] is False
        assert status["dispute_service"]["available"] is False


class TestWarnings:
    """Test warning generation"""

    @pytest.fixture
    def mock_tax_service(self):
        """Create mock tax service"""
        service = Mock()
        service.query = AsyncMock()

        # Mock response with invalid citations
        mock_response = Mock()
        mock_response.answer = "Test"
        mock_response.cited_articles = [
            Mock(article_number="999", title="Invalid", snippet="Test"),
        ]
        service.query.return_value = mock_response

        return service

    @pytest.mark.asyncio
    async def test_invalid_article_warning(self, mock_tax_service):
        """Test warning for invalid article numbers"""
        orchestrator = Orchestrator(tax_service=mock_tax_service)

        response = await orchestrator.route_query(
            message="test",
            mode=QueryMode.TAX
        )

        # Should have warning for invalid article
        assert len(response.warnings) > 0
        assert any("invalid" in warning.lower() for warning in response.warnings)


class TestKeywordMatching:
    """Test keyword matching utilities"""

    def test_get_matched_keywords(self):
        """Test keyword matching helper"""
        orchestrator = Orchestrator()

        message = "დღგ-ს განაკვეთი მუხლი 166"
        matched = orchestrator._get_matched_keywords(message, orchestrator.TAX_KEYWORDS)

        assert "დღგ" in matched
        assert "მუხლი" in matched
        assert "განაკვეთი" in matched

    def test_get_matched_keywords_case_insensitive(self):
        """Test keyword matching is case insensitive"""
        orchestrator = Orchestrator()

        message = "ДҒГ-С ᲒᲐᲜᲐᲙᲕᲔᲗᲘ ᲛᲣᲮᲚᲘ 166"
        matched = orchestrator._get_matched_keywords(message, orchestrator.TAX_KEYWORDS)

        # Should match despite case differences
        assert len(matched) > 0
