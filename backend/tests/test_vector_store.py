"""
Tests for Vector Store - FAISS and BM25 hybrid search
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List

from app.services.vector_store import VectorStore, Document, SearchResult


@pytest.fixture
def temp_index_dir():
    """Create temporary directory for index"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_documents() -> List[Document]:
    """Sample legal documents for testing"""
    return [
        Document(
            id="dispute_001",
            content="Tax court decision regarding VAT dispute. The court ruled that the 18% VAT rate applies according to article 166.",
            metadata={
                "case_id": "001",
                "court": "Supreme Court",
                "date": "2023-01-15",
                "cited_articles": ["166"]
            }
        ),
        Document(
            id="dispute_002",
            content="Income tax dispute case. The court examined the tax base calculation methodology according to article 168.",
            metadata={
                "case_id": "002",
                "court": "District Court",
                "date": "2023-02-20",
                "cited_articles": ["168"]
            }
        ),
        Document(
            id="dispute_003",
            content="Small business tax status case. Articles 84, 85, 86 define small business tax regime requirements.",
            metadata={
                "case_id": "003",
                "court": "Supreme Court",
                "date": "2023-03-10",
                "cited_articles": ["84", "85", "86"]
            }
        ),
    ]


class TestVectorStoreInitialization:
    """Test VectorStore initialization"""

    @pytest.mark.slow
    def test_creates_empty_index(self, temp_index_dir):
        """Test that VectorStore creates empty index on init"""
        store = VectorStore(index_path=temp_index_dir)

        assert store.faiss_index is not None
        assert len(store.documents) == 0

    @pytest.mark.slow
    def test_loads_existing_index(self, temp_index_dir, sample_documents):
        """Test that VectorStore loads existing index"""
        # Create and populate first store
        store1 = VectorStore(index_path=temp_index_dir)
        store1.add_documents(sample_documents)
        store1.save()

        # Create second store - should load existing
        store2 = VectorStore(index_path=temp_index_dir)

        assert len(store2.documents) == len(sample_documents)


class TestDocumentOperations:
    """Test document add/remove operations"""

    @pytest.mark.slow
    def test_add_documents(self, temp_index_dir, sample_documents):
        """Test adding documents to store"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        assert len(store.documents) == len(sample_documents)
        assert store.faiss_index.ntotal == len(sample_documents)

    @pytest.mark.slow
    def test_add_single_document(self, temp_index_dir):
        """Test adding a single document"""
        store = VectorStore(index_path=temp_index_dir)

        doc = Document(
            id="test_001",
            content="Test document content about tax law.",
            metadata={"type": "test"}
        )
        store.add_documents([doc])

        assert len(store.documents) == 1

    @pytest.mark.slow
    def test_clear_documents(self, temp_index_dir, sample_documents):
        """Test clearing all documents"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)
        store.clear()

        assert len(store.documents) == 0
        assert store.faiss_index.ntotal == 0


class TestVectorSearch:
    """Test vector similarity search"""

    @pytest.mark.slow
    def test_vector_search_returns_results(self, temp_index_dir, sample_documents):
        """Test that vector search returns relevant results"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = store.vector_search("VAT tax dispute", top_k=2)

        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].match_type == "vector"

    @pytest.mark.slow
    def test_vector_search_relevance_ordering(self, temp_index_dir, sample_documents):
        """Test that results are ordered by relevance"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = store.vector_search("VAT dispute article 166", top_k=3)

        # First result should be most relevant
        assert results[0].document.id == "dispute_001"
        # Scores should be in descending order
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score


class TestBM25Search:
    """Test BM25 keyword search"""

    @pytest.mark.slow
    def test_bm25_search_returns_results(self, temp_index_dir, sample_documents):
        """Test that BM25 search returns results"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = store.bm25_search("article 166", top_k=2)

        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].match_type == "bm25"

    @pytest.mark.slow
    def test_bm25_exact_match_priority(self, temp_index_dir, sample_documents):
        """Test that exact keyword matches are prioritized"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = store.bm25_search("small business tax", top_k=3)

        # Document about small business should be first
        assert results[0].document.id == "dispute_003"


class TestHybridSearch:
    """Test hybrid search combining vector and BM25"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_hybrid_search_returns_results(self, temp_index_dir, sample_documents):
        """Test that hybrid search returns results"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = await store.hybrid_search("VAT tax dispute", top_k=2)

        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].match_type == "hybrid"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_hybrid_search_with_filter(self, temp_index_dir, sample_documents):
        """Test hybrid search with metadata filter"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = await store.hybrid_search(
            "tax dispute",
            top_k=3,
            filter_metadata={"court": "Supreme Court"}
        )

        # All results should be from Supreme Court
        for result in results:
            assert result.document.metadata.get("court") == "Supreme Court"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_hybrid_search_empty_query(self, temp_index_dir, sample_documents):
        """Test hybrid search with empty query returns empty results"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        results = await store.hybrid_search("", top_k=2)

        assert len(results) == 0


class TestPersistence:
    """Test index save/load operations"""

    @pytest.mark.slow
    def test_save_and_load_index(self, temp_index_dir, sample_documents):
        """Test saving and loading the index"""
        # Create and save
        store1 = VectorStore(index_path=temp_index_dir)
        store1.add_documents(sample_documents)
        store1.save()

        # Load in new instance
        store2 = VectorStore(index_path=temp_index_dir)

        assert len(store2.documents) == len(sample_documents)
        assert store2.faiss_index.ntotal == len(sample_documents)

    @pytest.mark.slow
    def test_index_persistence_files_created(self, temp_index_dir, sample_documents):
        """Test that persistence files are created"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)
        store.save()

        index_path = Path(temp_index_dir)
        assert (index_path / "faiss.index").exists()
        assert (index_path / "documents.pkl").exists()
        assert (index_path / "bm25_index.pkl").exists()


class TestStatistics:
    """Test statistics and info methods"""

    @pytest.mark.slow
    def test_get_stats(self, temp_index_dir, sample_documents):
        """Test getting store statistics"""
        store = VectorStore(index_path=temp_index_dir)
        store.add_documents(sample_documents)

        stats = store.get_stats()

        assert stats["total_documents"] == len(sample_documents)
        assert "embedding_model" in stats
        assert "index_path" in stats
