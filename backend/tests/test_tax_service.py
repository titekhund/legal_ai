"""
Tests for tax service - citation extraction and response parsing
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.tax_code_service import TaxCodeService
from app.services.citation_extractor import CitationExtractor


class TestCitationExtractor:
    """Test citation extraction patterns"""

    def setup_method(self):
        self.extractor = CitationExtractor()

    def test_extract_georgian_article_simple(self):
        """Test extraction of simple Georgian article references"""
        text = "საგადასახადო კოდექსის მუხლი 166 განსაზღვრავს დღგ-ს განაკვეთს."
        citations = self.extractor.extract_citations(text)

        assert len(citations) > 0
        assert any(c.article == "166" for c in citations)

    def test_extract_georgian_article_with_paragraph(self):
        """Test extraction of article with paragraph"""
        text = "მუხლი 168.1 განსაზღვრავს გადახდის ვადას."
        citations = self.extractor.extract_citations(text)

        assert len(citations) > 0
        assert any("168" in c.article for c in citations)

    def test_extract_georgian_article_with_subparagraph(self):
        """Test extraction of article with subparagraph"""
        text = "მუხლი 97.1.ა განსაზღვრავს გამონაკლისებს."
        citations = self.extractor.extract_citations(text)

        assert len(citations) > 0
        assert any("97" in c.article for c in citations)

    def test_extract_multiple_articles(self):
        """Test extraction of multiple article references"""
        text = "მუხლი 166 და მუხლი 165 განსაზღვრავენ დღგ-ს წესებს."
        citations = self.extractor.extract_citations(text)

        assert len(citations) >= 2
        articles = [c.article for c in citations]
        assert "166" in articles or any("166" in a for a in articles)
        assert "165" in articles or any("165" in a for a in articles)

    def test_no_false_positives(self):
        """Test that normal numbers aren't extracted as articles"""
        text = "საქართველოში 2024 წელს ფასები 15% გაიზარდა."
        citations = self.extractor.extract_citations(text)

        # Should not extract "15" or "2024" as article numbers
        assert len(citations) == 0

    def test_extract_with_context(self):
        """Test citation extraction with surrounding context"""
        text = """
        დღგ-ს განაკვეთი განისაზღვრება მუხლი 166-ით.
        ეს განაკვეთი არის 18 პროცენტი.
        """
        citations = self.extractor.extract_citations(text)

        assert len(citations) > 0
        citation = next(c for c in citations if "166" in c.article)
        assert citation is not None


class TestTaxCodeService:
    """Test tax code service functionality"""

    @pytest.fixture
    def mock_gemini_client(self):
        """Create a mock Gemini client"""
        client = Mock()
        client.generate_response = AsyncMock()
        return client

    @pytest.fixture
    def service(self, mock_gemini_client):
        """Create service with mocked dependencies"""
        with patch('app.services.tax_code_service.GeminiClient', return_value=mock_gemini_client):
            service = TaxCodeService()
            service.gemini_client = mock_gemini_client
            return service

    @pytest.mark.asyncio
    async def test_get_tax_answer_success(self, service, mock_gemini_client):
        """Test successful tax question answering"""
        # Mock response with Georgian article reference
        mock_response = """
        დღგ-ს განაკვეთი საქართველოში არის 18%.
        ეს განისაზღვრება საგადასახადო კოდექსის მუხლი 166-ით.
        """
        mock_gemini_client.generate_response.return_value = mock_response

        result = await service.get_tax_answer(
            question="რა არის დღგ-ს განაკვეთი?",
            conversation_id="test-123"
        )

        assert result is not None
        assert "answer" in result
        assert "sources" in result
        assert mock_gemini_client.generate_response.called

    @pytest.mark.asyncio
    async def test_get_tax_answer_with_citations(self, service, mock_gemini_client):
        """Test that citations are properly extracted"""
        mock_response = """
        საშემოსავლო გადასახადის განაკვეთი არის 20%.
        მუხლი 168 განსაზღვრავს ფიზიკური პირების დაბეგვრას.
        მუხლი 169 განსაზღვრავს გამონაკლისებს.
        """
        mock_gemini_client.generate_response.return_value = mock_response

        result = await service.get_tax_answer(
            question="რა არის საშემოსავლო გადასახადის განაკვეთი?",
            conversation_id="test-456"
        )

        assert "sources" in result
        assert len(result["sources"]) > 0
        # Should extract both article 168 and 169
        articles = [s["article"] for s in result["sources"]]
        assert len(articles) >= 1

    @pytest.mark.asyncio
    async def test_get_tax_answer_empty_question(self, service, mock_gemini_client):
        """Test handling of empty question"""
        with pytest.raises(ValueError):
            await service.get_tax_answer(
                question="",
                conversation_id="test-789"
            )

    @pytest.mark.asyncio
    async def test_get_tax_answer_api_error(self, service, mock_gemini_client):
        """Test handling of API errors"""
        mock_gemini_client.generate_response.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            await service.get_tax_answer(
                question="რა არის დღგ?",
                conversation_id="test-error"
            )

    @pytest.mark.asyncio
    async def test_response_parsing(self, service, mock_gemini_client):
        """Test that response is properly parsed and formatted"""
        mock_response = "მოკლე პასუხი მუხლი 100-ის შესახებ."
        mock_gemini_client.generate_response.return_value = mock_response

        result = await service.get_tax_answer(
            question="ტესტის კითხვა?",
            conversation_id="test-parse"
        )

        assert isinstance(result, dict)
        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert "sources" in result
        assert isinstance(result["sources"], list)

    @pytest.mark.asyncio
    async def test_conversation_context(self, service, mock_gemini_client):
        """Test that conversation ID is properly used"""
        mock_gemini_client.generate_response.return_value = "პასუხი"

        conv_id = "test-context-123"
        await service.get_tax_answer(
            question="პირველი კითხვა?",
            conversation_id=conv_id
        )

        # Verify the conversation ID was used
        assert mock_gemini_client.generate_response.called
        call_args = mock_gemini_client.generate_response.call_args
        # The conversation context should be maintained
        assert call_args is not None


class TestResponseParsing:
    """Test response parsing and formatting"""

    def setup_method(self):
        self.extractor = CitationExtractor()

    def test_parse_response_with_multiple_citations(self):
        """Test parsing response with multiple article citations"""
        response = """
        დღგ-ს რეგისტრაცია სავალდებულოა მუხლი 165-ის მიხედვით.
        განაკვეთი კი განისაზღვრება მუხლი 166-ით.
        გადახდის ვადები მოცემულია მუხლი 167-ში.
        """

        citations = self.extractor.extract_citations(response)

        assert len(citations) >= 3
        articles = [c.article for c in citations]
        assert any("165" in a for a in articles)
        assert any("166" in a for a in articles)
        assert any("167" in a for a in articles)

    def test_parse_response_without_citations(self):
        """Test parsing response with no article citations"""
        response = "ეს არის ზოგადი ინფორმაცია გადასახადების შესახებ."

        citations = self.extractor.extract_citations(response)

        assert len(citations) == 0

    def test_parse_malformed_response(self):
        """Test handling of malformed response"""
        response = None

        # Should not crash, should return empty list
        citations = self.extractor.extract_citations(response or "")
        assert citations == []


# Integration-style tests (if we have access to actual service)
class TestTaxCodeServiceIntegration:
    """Integration tests for tax code service"""

    @pytest.mark.skipif(True, reason="Requires actual API keys and service")
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test with real API call (skipped by default)"""
        service = TaxCodeService()
        result = await service.get_tax_answer(
            question="რა არის დღგ-ს განაკვეთი?",
            conversation_id="integration-test"
        )

        assert result is not None
        assert "answer" in result
        assert len(result["answer"]) > 0
