"""
Tests for Dispute RAG Service
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil
import numpy as np

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
            content="����������� �������� ���-� ���� �� ��������, ��� ��������� ���� ���� 18% ����� 166-�� ��������.",
            metadata={
                "case_id": "001",
                "court": "�������� ����������",
                "date": "2023-05-15",
                "cited_articles": ["166"]
            }
        ),
        Document(
            id="dispute_002",
            content="����������� ����������� ������ ����������� ����� ������� ����������� ����������.",
            metadata={
                "case_id": "002",
                "court": "�������� ����������",
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
    client.generate_response.return_value = "���-� ��������� ���� 18 ��������, ������ �� ������������� ����� 166-��. ����� #001 (2023-05-15) ���������� �� ���������."
    return client


class TestDisputeFilters:
    """Test DisputeFilters model"""

    def test_filters_creation(self):
        """Test creating dispute filters"""
        filters = DisputeFilters(
            court="�������� ����������",
            date_from=date(2023, 1, 1),
            date_to=date(2023, 12, 31),
            cited_articles=["166", "168"]
        )

        assert filters.court == "�������� ����������"
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
            court="�������� ����������",
            date=date(2023, 5, 15),
            summary="Test summary",
            cited_articles=["166"],
            relevance_score=0.92,
            full_text_available=True
        )

        assert case.case_id == "001"
        assert case.court == "�������� ����������"
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

        response = await service.query("�� ���� ���-� ���������?")

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
            court="�������� ����������",
            date_from=date(2023, 1, 1)
        )

        response = await service.query("���", filters=filters)

        assert isinstance(response, DisputeResponse)
        # Cases should be filtered by court
        for case in response.cases_cited:
            assert case.court == "�������� ����������"

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

        assert response.answer == "��� �������� ����������� �������� ������ �����������."
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
        assert "��� ��������" in response.answer
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
        assert case.court == "�������� ����������"
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

        text = "����� 166 �� ����� 168 ������������ ���-� ������. ����� 82.1 ����� ��������������."
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
                court="�������� ����������",
                date=date(2023, 5, 15),
                summary="Test case summary",
                cited_articles=["166"],
                relevance_score=0.9,
                full_text_available=True
            )
        ]

        context = service._build_context(cases)

        assert "����� #1" in context
        assert "001" in context
        assert "�������� ����������" in context
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


class TestVectorStore:
    """Test Vector Store search functionality with mocked embeddings"""

    @pytest.fixture
    def mock_embedding_model(self):
        """Mock sentence transformer to avoid downloading models"""
        mock_model = Mock()
        # Return deterministic embeddings for testing
        def mock_encode(texts, convert_to_numpy=False):
            # Simple hash-based embeddings for testing
            embeddings = []
            for text in texts:
                # Create a deterministic but varied embedding based on text
                hash_val = hash(text) % 1000
                embedding = np.array([float(hash_val % (i+1)) for i in range(384)])
                embedding = embedding / np.linalg.norm(embedding)  # Normalize
                embeddings.append(embedding)
            return np.array(embeddings)

        mock_model.encode = Mock(side_effect=mock_encode)
        return mock_model

    @pytest.mark.asyncio
    async def test_vector_search(self, temp_index_dir, mock_embedding_model):
        """Test pure vector similarity search"""
        with patch('app.services.vector_store.SentenceTransformer', return_value=mock_embedding_model):
            store = VectorStore(index_path=temp_index_dir)

            # Add documents
            documents = [
                Document(
                    id="vec_001",
                    content="დღგ-ს განაკვეთი არის 18 პროცენტი საქართველოში",
                    metadata={"topic": "vat_rate", "date": "2023-01-15"}
                ),
                Document(
                    id="vec_002",
                    content="საშემოსავლო გადასახადის განაკვეთი არის 20 პროცენტი",
                    metadata={"topic": "income_tax", "date": "2023-02-20"}
                ),
                Document(
                    id="vec_003",
                    content="დღგ-ის ჩათვლა შესაძლებელია მუხლი 166-ის მიხედვით",
                    metadata={"topic": "vat_deduction", "date": "2023-03-10"}
                )
            ]

            await store.add_documents(documents)

            # Search for VAT-related content
            results = await store.search("დღგ განაკვეთი რა არის?", top_k=2)

            assert len(results) > 0
            assert all(r.match_type == "vector" for r in results)
            assert all(0 <= r.score <= 1 for r in results)
            # Results should be sorted by score
            if len(results) > 1:
                assert results[0].score >= results[1].score

    @pytest.mark.asyncio
    async def test_bm25_search(self, temp_index_dir, mock_embedding_model):
        """Test BM25 keyword search"""
        with patch('app.services.vector_store.SentenceTransformer', return_value=mock_embedding_model):
            store = VectorStore(index_path=temp_index_dir)

            # Add documents with distinctive keywords
            documents = [
                Document(
                    id="bm25_001",
                    content="დოკუმენტის # ТД-2023-100 დღგ-ის ჩათვლის შესახებ მუხლი 166",
                    metadata={"doc_number": "ТД-2023-100"}
                ),
                Document(
                    id="bm25_002",
                    content="დოკუმენტის # ТД-2023-101 საშემოსავლო გადასახადი მუხლი 168",
                    metadata={"doc_number": "ТД-2023-101"}
                ),
                Document(
                    id="bm25_003",
                    content="დოკუმენტის # ТД-2023-102 დღგ ჩათვლა უარი დამრიცხველი ორგანო",
                    metadata={"doc_number": "ТД-2023-102"}
                )
            ]

            await store.add_documents(documents)

            # BM25 search with specific keywords
            results = await store.bm25_search("დღგ ჩათვლა", top_k=2)

            assert len(results) > 0
            assert all(r.match_type == "bm25" for r in results)
            assert all(0 <= r.score <= 1 for r in results)
            # Should find documents with "დღგ" and "ჩათვლა" keywords

    @pytest.mark.asyncio
    async def test_hybrid_search(self, temp_index_dir, mock_embedding_model):
        """Test hybrid search combining vector and BM25"""
        with patch('app.services.vector_store.SentenceTransformer', return_value=mock_embedding_model):
            store = VectorStore(index_path=temp_index_dir)

            # Add diverse documents
            documents = [
                Document(
                    id="hyb_001",
                    content="მუხლი 166 განსაზღვრავს დღგ-ს განაკვეთს 18 პროცენტად",
                    metadata={"article": "166", "category": "დღგ"}
                ),
                Document(
                    id="hyb_002",
                    content="საბჭოს გადაწყვეტილება დღგ-ის ჩათვლის უფლების შესახებ",
                    metadata={"article": "166", "category": "დავა"}
                ),
                Document(
                    id="hyb_003",
                    content="მუხლი 168 საშემოსავლო გადასახადის შესახებ",
                    metadata={"article": "168", "category": "საშემოსავლო"}
                )
            ]

            await store.add_documents(documents)

            # Hybrid search should combine semantic and keyword matching
            results = await store.hybrid_search(
                query="დღგ ჩათვლა მუხლი 166",
                top_k=3,
                vector_weight=0.5,
                bm25_weight=0.5
            )

            assert len(results) > 0
            assert all(r.match_type == "hybrid" for r in results)
            assert all(0 <= r.score <= 1 for r in results)
            # Hybrid scores should be sorted descending
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i].score >= results[i+1].score

    @pytest.mark.asyncio
    async def test_metadata_filtering(self, temp_index_dir, mock_embedding_model):
        """Test vector search with metadata filters"""
        with patch('app.services.vector_store.SentenceTransformer', return_value=mock_embedding_model):
            store = VectorStore(index_path=temp_index_dir)

            # Add documents with different categories
            documents = [
                Document(
                    id="filter_001",
                    content="დღგ-ს განაკვეთი კატეგორია A",
                    metadata={"category": "დღგ", "year": "2023"}
                ),
                Document(
                    id="filter_002",
                    content="დღგ-ს განაკვეთი კატეგორია B",
                    metadata={"category": "საშემოსავლო", "year": "2023"}
                ),
                Document(
                    id="filter_003",
                    content="დღგ-ს განაკვეთი კატეგორია C",
                    metadata={"category": "დღგ", "year": "2024"}
                )
            ]

            await store.add_documents(documents)

            # Search with metadata filter
            results = await store.search(
                query="დღგ განაკვეთი",
                top_k=5,
                filter_metadata={"category": "დღგ"}
            )

            # All results should match the filter
            assert all(r.document.metadata.get("category") == "დღგ" for r in results)
            # Should exclude filter_002 (category: საშემოსავლო)
            doc_ids = [r.document.id for r in results]
            assert "filter_002" not in doc_ids

    @pytest.mark.asyncio
    async def test_hybrid_search_with_weights(self, temp_index_dir, mock_embedding_model):
        """Test hybrid search with different weight configurations"""
        with patch('app.services.vector_store.SentenceTransformer', return_value=mock_embedding_model):
            store = VectorStore(index_path=temp_index_dir)

            documents = [
                Document(
                    id="weight_001",
                    content="დღგ განაკვეთი საქართველოში არის ათი რვა პროცენტი",
                    metadata={"type": "explanation"}
                ),
                Document(
                    id="weight_002",
                    content="მუხლი 166 დღგ",
                    metadata={"type": "reference"}
                )
            ]

            await store.add_documents(documents)

            # Test with vector-heavy weighting
            vector_heavy = await store.hybrid_search(
                query="რა არის დღგ-ს განაკვეთი?",
                top_k=2,
                vector_weight=0.8,
                bm25_weight=0.2
            )

            # Test with BM25-heavy weighting
            bm25_heavy = await store.hybrid_search(
                query="მუხლი 166 დღგ",
                top_k=2,
                vector_weight=0.2,
                bm25_weight=0.8
            )

            assert len(vector_heavy) > 0
            assert len(bm25_heavy) > 0
            # Both should return results, but potentially in different order


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
        assert "��������" in prompt
