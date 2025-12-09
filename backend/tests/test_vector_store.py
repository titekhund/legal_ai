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
def sample_georgian_documents() -> List[Document]:
    """Sample Georgian legal documents for testing"""
    return [
        Document(
            id="dispute_001",
            content="сасаларзкнл вамиюика гцв-с гаеа га гаагвима, рнл вамайедзи умга ичнс 18 орнъдмти луюки 166-ис лиюдгеиз.",
            metadata={
                "case_id": "001",
                "court": "уждмадси сасаларзкн",
                "date": "2023-01-15",
                "cited_articles": ["166"]
            }
        ),
        Document(
            id="dispute_002",
            content="сашдлнсаекн вагасаюагис гаеаши сасаларзкнл люари гауэира вагасаюагис вагалюгдкс. луюки 168 вамсажцераес фижийури оирис сашдлнсаекн вагасаюагс.",
            metadata={
                "case_id": "002",
                "court": "сахакахн сасаларзкн",
                "date": "2023-02-20",
                "cited_articles": ["168"]
            }
        ),
        Document(
            id="dispute_003",
            content="лийрн бижмдсис статусис лимиэдбис гаеа. луюки 84, 85, 86 вамсажцераес лийрн бижмдсис йритдриулдбс га шдлнсаекис жцеарс 30,000 кари.",
            metadata={
                "case_id": "003",
                "court": "сааодкаъин сасаларзкн",
                "date": "2023-03-10",
                "cited_articles": ["84", "85", "86"]
            }
        ),
        Document(
            id="dispute_004",
            content="аетнлнбикис вачигеис габдвера. луюки 82 вамсажцераес, рнл аетнлнбикис вачигеа 6 зеис вамлаекнбаши ибдврдба.",
            metadata={
                "case_id": "004",
                "court": "уждмадси сасаларзкн",
                "date": "2023-04-05",
                "cited_articles": ["82"]
            }
        ),
        Document(
            id="dispute_005",
            content="бимис рдакижаъиа га вагасаюаги. сасаларзкнл вамларта, рнл бимис вачигеа заеисуфкгдба вагасаюагисвам зу гаиэира 2 ьдкжд лдти.",
            metadata={
                "case_id": "005",
                "court": "сахакахн сасаларзкн",
                "date": "2023-05-12",
                "cited_articles": ["82"]
            }
        )
    ]


class TestDocument:
    """Test Document model"""

    def test_document_creation(self):
        """Test creating a document"""
        doc = Document(
            id="test_001",
            content="тдстис шимаарси",
            metadata={"case_id": "001"}
        )

        assert doc.id == "test_001"
        assert doc.content == "тдстис шимаарси"
        assert doc.metadata["case_id"] == "001"
        assert doc.embedding is None

    def test_document_with_embedding(self):
        """Test document with pre-computed embedding"""
        embedding = [0.1, 0.2, 0.3]
        doc = Document(
            id="test_001",
            content="тдсти",
            metadata={},
            embedding=embedding
        )

        assert doc.embedding == embedding


class TestSearchResult:
    """Test SearchResult model"""

    def test_search_result_creation(self):
        """Test creating a search result"""
        doc = Document(id="test", content="test", metadata={})
        result = SearchResult(
            document=doc,
            score=0.95,
            match_type="hybrid"
        )

        assert result.document.id == "test"
        assert result.score == 0.95
        assert result.match_type == "hybrid"


class TestVectorStore:
    """Test VectorStore functionality"""

    @pytest.mark.asyncio
    async def test_initialization(self, temp_index_dir):
        """Test vector store initialization"""
        store = VectorStore(
            index_path=temp_index_dir,
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        assert store is not None
        assert store.encoder is not None
        assert store.faiss_index is not None
        assert len(store.documents) == 0

    @pytest.mark.asyncio
    async def test_add_documents(self, temp_index_dir, sample_georgian_documents):
        """Test adding documents to the store"""
        store = VectorStore(index_path=temp_index_dir)

        count = await store.add_documents(sample_georgian_documents)

        assert count == len(sample_georgian_documents)
        assert len(store.documents) == len(sample_georgian_documents)
        assert store.bm25 is not None

        # Verify embeddings were generated
        for doc in store.documents:
            assert doc.embedding is not None
            assert len(doc.embedding) == 384  # MiniLM-L12 dimension

    @pytest.mark.asyncio
    async def test_add_empty_documents(self, temp_index_dir):
        """Test adding empty document list"""
        store = VectorStore(index_path=temp_index_dir)

        count = await store.add_documents([])

        assert count == 0
        assert len(store.documents) == 0

    @pytest.mark.asyncio
    async def test_vector_search(self, temp_index_dir, sample_georgian_documents):
        """Test vector similarity search"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        # Search for VAT related content
        results = await store.search("гцв-с вамайедзи", top_k=3)

        assert len(results) > 0
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.match_type == "vector" for r in results)
        assert all(0 <= r.score <= 1 for r in results)

        # First result should be dispute_001 (VAT rate case)
        assert results[0].document.id == "dispute_001"

    @pytest.mark.asyncio
    async def test_bm25_search(self, temp_index_dir, sample_georgian_documents):
        """Test BM25 keyword search"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        # Search for specific keywords
        results = await store.bm25_search("луюки 166", top_k=2)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.match_type == "bm25" for r in results)

        # Should find dispute_001 which mentions article 166
        doc_ids = [r.document.id for r in results]
        assert "dispute_001" in doc_ids

    @pytest.mark.asyncio
    async def test_hybrid_search(self, temp_index_dir, sample_georgian_documents):
        """Test hybrid search combining vector and BM25"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        # Search with both semantic and keyword matching
        results = await store.hybrid_search("гцв-с рдвистраъиа", top_k=3)

        assert len(results) > 0
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.match_type == "hybrid" for r in results)
        assert all(0 <= r.score <= 1 for r in results)

    @pytest.mark.asyncio
    async def test_hybrid_search_with_weights(self, temp_index_dir, sample_georgian_documents):
        """Test hybrid search with custom weights"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        # Favor BM25
        results_bm25 = await store.hybrid_search(
            "луюки 166",
            top_k=3,
            vector_weight=0.2,
            bm25_weight=0.8
        )

        # Favor vector
        results_vector = await store.hybrid_search(
            "луюки 166",
            top_k=3,
            vector_weight=0.8,
            bm25_weight=0.2
        )

        assert len(results_bm25) > 0
        assert len(results_vector) > 0

        # Results may differ based on weighting
        # Just verify they return valid results

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self, temp_index_dir, sample_georgian_documents):
        """Test search with metadata filtering"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        # Search only in Supreme Court cases
        results = await store.search(
            "вагасаюаги",
            top_k=5,
            filter_metadata={"court": "уждмадси сасаларзкн"}
        )

        assert len(results) > 0
        # All results should be from Supreme Court
        assert all(r.document.metadata.get("court") == "уждмадси сасаларзкн" for r in results)

    @pytest.mark.asyncio
    async def test_search_empty_index(self, temp_index_dir):
        """Test search on empty index"""
        store = VectorStore(index_path=temp_index_dir)

        results = await store.search("test query")

        assert len(results) == 0

    def test_tokenize_georgian_text(self, temp_index_dir):
        """Test Georgian text tokenization"""
        store = VectorStore(index_path=temp_index_dir)

        text = "сасаларзкнл вамиюика гцв-с гаеа, луюки 166."
        tokens = store._tokenize_text(text)

        assert len(tokens) > 0
        assert "сасаларзкнл" in tokens
        assert "вамиюика" in tokens
        assert "гцв" in tokens
        assert "луюки" in tokens
        assert "166" in tokens

    def test_save_and_load(self, temp_index_dir, sample_georgian_documents):
        """Test saving and loading index"""
        # Create and populate store
        store1 = VectorStore(index_path=temp_index_dir)
        import asyncio
        asyncio.run(store1.add_documents(sample_georgian_documents))

        original_doc_count = len(store1.documents)

        # Save
        store1.save()

        # Load in new store instance
        store2 = VectorStore(index_path=temp_index_dir)

        assert len(store2.documents) == original_doc_count
        assert store2.faiss_index is not None
        assert store2.bm25 is not None

        # Verify we can search after loading
        results = asyncio.run(store2.search("гцв"))
        assert len(results) > 0

    def test_get_stats(self, temp_index_dir, sample_georgian_documents):
        """Test getting vector store statistics"""
        store = VectorStore(index_path=temp_index_dir)
        import asyncio
        asyncio.run(store.add_documents(sample_georgian_documents))

        stats = store.get_stats()

        assert stats["total_documents"] == len(sample_georgian_documents)
        assert stats["embedding_dim"] == 384
        assert stats["faiss_index_size"] == len(sample_georgian_documents)
        assert stats["bm25_initialized"] is True
        assert "paraphrase-multilingual-MiniLM-L12-v2" in stats["embedding_model"]


class TestVectorStoreEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, temp_index_dir, sample_georgian_documents):
        """Test search with special characters"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        # Query with punctuation and numbers
        results = await store.search("луюки 166, 168-ис шдсаюдб!", top_k=3)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_with_very_long_query(self, temp_index_dir, sample_georgian_documents):
        """Test search with very long query"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        long_query = "гцв " * 100  # Very long query
        results = await store.search(long_query, top_k=3)

        # Should still work, not crash
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_add_duplicate_documents(self, temp_index_dir):
        """Test adding documents with duplicate IDs"""
        store = VectorStore(index_path=temp_index_dir)

        doc1 = Document(id="dup", content="first", metadata={})
        doc2 = Document(id="dup", content="second", metadata={})

        await store.add_documents([doc1])
        await store.add_documents([doc2])

        # Both should be added (no deduplication by default)
        assert len(store.documents) == 2

    @pytest.mark.asyncio
    async def test_search_top_k_larger_than_corpus(self, temp_index_dir, sample_georgian_documents):
        """Test search with top_k larger than available documents"""
        store = VectorStore(index_path=temp_index_dir)
        await store.add_documents(sample_georgian_documents)

        results = await store.search("test", top_k=100)

        # Should return all available documents, not crash
        assert len(results) <= len(sample_georgian_documents)
