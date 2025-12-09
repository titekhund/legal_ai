"""
Vector Store for Dispute Documents using FAISS and BM25 Hybrid Search

This module implements a hybrid search system combining:
1. FAISS for dense vector similarity search
2. BM25 for sparse keyword-based retrieval
3. Support for Georgian text via multilingual sentence transformers
"""

import pickle
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

import numpy as np
import faiss
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Document(BaseModel):
    """Document model for vector store"""
    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document text content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (case_id, court, date, cited_articles, etc.)"
    )
    embedding: Optional[List[float]] = Field(
        None,
        description="Pre-computed embedding vector"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "dispute_001",
                "content": "сасаларзкн вагаьчедтикдба гцв-с гаеис шдсаюдб...",
                "metadata": {
                    "case_id": "001",
                    "court": "сахарзедкнс уждмадси сасаларзкн",
                    "date": "2023-05-15",
                    "cited_articles": ["166", "165"]
                }
            }
        }


class SearchResult(BaseModel):
    """Search result model"""
    document: Document = Field(..., description="Retrieved document")
    score: float = Field(..., description="Relevance score")
    match_type: str = Field(
        ...,
        description="Type of match: 'vector', 'bm25', or 'hybrid'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document": {
                    "id": "dispute_001",
                    "content": "сасаларзкн вагаьчедтикдба...",
                    "metadata": {"case_id": "001"}
                },
                "score": 0.89,
                "match_type": "hybrid"
            }
        }


class VectorStore:
    """
    Hybrid vector store using FAISS and BM25

    Combines dense vector embeddings with sparse keyword matching
    for improved retrieval quality, especially for Georgian legal text.
    """

    def __init__(
        self,
        index_path: str,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        embedding_dim: int = 384
    ):
        """
        Initialize vector store

        Args:
            index_path: Directory path for storing FAISS and BM25 indices
            embedding_model: Sentence-transformers model name
            embedding_dim: Dimension of embedding vectors (384 for MiniLM-L12)
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.embedding_model_name = embedding_model
        self.embedding_dim = embedding_dim

        # Initialize sentence transformer
        logger.info(f"Loading embedding model: {embedding_model}")
        self.encoder = SentenceTransformer(embedding_model)

        # Initialize FAISS index
        self.faiss_index = None
        self.documents: List[Document] = []

        # Initialize BM25
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

        # Paths for persistence
        self.faiss_index_path = self.index_path / "faiss.index"
        self.documents_path = self.index_path / "documents.pkl"
        self.bm25_path = self.index_path / "bm25_index.pkl"

        # Try to load existing index
        try:
            self.load()
            logger.info(f"Loaded existing index with {len(self.documents)} documents")
        except FileNotFoundError:
            logger.info("No existing index found, creating new one")
            self._initialize_empty_index()

    def _initialize_empty_index(self):
        """Initialize empty FAISS index"""
        # Use L2 distance for similarity
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        logger.info(f"Initialized empty FAISS index with dimension {self.embedding_dim}")

    def _tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text for BM25

        Handles Georgian text by splitting on whitespace and punctuation
        while preserving Georgian characters.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Convert to lowercase for better matching
        text = text.lower()

        # Split on whitespace and punctuation, but keep Georgian letters
        # Georgian Unicode range: \u10A0-\u10FF
        tokens = re.findall(r'[\u10A0-\u10FFa-z0-9]+', text)

        return tokens

    async def add_documents(self, documents: List[Document]) -> int:
        """
        Add documents to the vector store

        Args:
            documents: List of documents to add

        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        logger.info(f"Adding {len(documents)} documents to vector store")

        # Generate embeddings for documents that don't have them
        texts_to_embed = []
        docs_to_embed = []

        for doc in documents:
            if doc.embedding is None:
                texts_to_embed.append(doc.content)
                docs_to_embed.append(doc)

        if texts_to_embed:
            logger.info(f"Generating embeddings for {len(texts_to_embed)} documents")
            embeddings = self.encoder.encode(
                texts_to_embed,
                show_progress_bar=True,
                convert_to_numpy=True
            )

            # Assign embeddings to documents
            for doc, embedding in zip(docs_to_embed, embeddings):
                doc.embedding = embedding.tolist()

        # Add to FAISS index
        embeddings_array = np.array([doc.embedding for doc in documents], dtype=np.float32)
        self.faiss_index.add(embeddings_array)

        # Add to documents list
        self.documents.extend(documents)

        # Rebuild BM25 index
        self.tokenized_corpus = [self._tokenize_text(doc.content) for doc in self.documents]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        logger.info(f"Successfully added {len(documents)} documents. Total: {len(self.documents)}")

        # Auto-save after adding documents
        self.save()

        return len(documents)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Vector similarity search using FAISS

        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of search results sorted by relevance
        """
        if not self.documents:
            logger.warning("No documents in index")
            return []

        # Generate query embedding
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)

        # Search FAISS index
        # Note: FAISS returns L2 distances, lower is better
        distances, indices = self.faiss_index.search(query_embedding, min(top_k * 2, len(self.documents)))

        # Convert distances to similarity scores (inverse of L2 distance)
        # Normalize to 0-1 range
        max_distance = distances[0].max() if distances[0].max() > 0 else 1.0
        similarities = 1 - (distances[0] / max_distance)

        # Build results
        results = []
        for idx, score in zip(indices[0], similarities):
            if idx < 0 or idx >= len(self.documents):
                continue

            doc = self.documents[idx]

            # Apply metadata filters if provided
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue

            results.append(SearchResult(
                document=doc,
                score=float(score),
                match_type="vector"
            ))

        # Sort by score descending and limit to top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    async def bm25_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        BM25 keyword search

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of search results sorted by BM25 score
        """
        if not self.bm25 or not self.documents:
            logger.warning("BM25 index not initialized or no documents")
            return []

        # Tokenize query
        tokenized_query = self._tokenize_text(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Build results
        results = []
        max_score = scores.max() if scores.max() > 0 else 1.0

        for idx in top_indices:
            if scores[idx] <= 0:
                continue

            results.append(SearchResult(
                document=self.documents[idx],
                score=float(scores[idx] / max_score),  # Normalize to 0-1
                match_type="bm25"
            ))

        return results

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Hybrid search combining vector and BM25 scores

        Args:
            query: Search query text
            top_k: Number of results to return
            vector_weight: Weight for vector similarity (default 0.5)
            bm25_weight: Weight for BM25 score (default 0.5)
            filter_metadata: Optional metadata filters

        Returns:
            List of search results with combined scores
        """
        if not self.documents:
            logger.warning("No documents in index")
            return []

        # Get vector search results
        vector_results = await self.search(query, top_k=top_k * 2, filter_metadata=filter_metadata)

        # Get BM25 results
        bm25_results = await self.bm25_search(query, top_k=top_k * 2)

        # Combine scores
        combined_scores: Dict[str, Dict[str, Any]] = {}

        # Add vector scores
        for result in vector_results:
            doc_id = result.document.id
            combined_scores[doc_id] = {
                "document": result.document,
                "vector_score": result.score,
                "bm25_score": 0.0
            }

        # Add BM25 scores
        for result in bm25_results:
            doc_id = result.document.id
            if doc_id in combined_scores:
                combined_scores[doc_id]["bm25_score"] = result.score
            else:
                combined_scores[doc_id] = {
                    "document": result.document,
                    "vector_score": 0.0,
                    "bm25_score": result.score
                }

        # Calculate combined scores
        hybrid_results = []
        for doc_id, scores in combined_scores.items():
            combined_score = (
                vector_weight * scores["vector_score"] +
                bm25_weight * scores["bm25_score"]
            )

            # Apply metadata filters
            if filter_metadata:
                doc = scores["document"]
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue

            hybrid_results.append(SearchResult(
                document=scores["document"],
                score=combined_score,
                match_type="hybrid"
            ))

        # Sort by combined score
        hybrid_results.sort(key=lambda x: x.score, reverse=True)

        return hybrid_results[:top_k]

    def save(self):
        """Persist index to disk"""
        logger.info(f"Saving vector store to {self.index_path}")

        # Save FAISS index
        if self.faiss_index is not None:
            faiss.write_index(self.faiss_index, str(self.faiss_index_path))
            logger.info(f"Saved FAISS index to {self.faiss_index_path}")

        # Save documents
        with open(self.documents_path, 'wb') as f:
            pickle.dump(self.documents, f)
        logger.info(f"Saved {len(self.documents)} documents to {self.documents_path}")

        # Save BM25 index
        if self.bm25 is not None:
            with open(self.bm25_path, 'wb') as f:
                pickle.dump({
                    "bm25": self.bm25,
                    "tokenized_corpus": self.tokenized_corpus
                }, f)
            logger.info(f"Saved BM25 index to {self.bm25_path}")

    def load(self):
        """Load index from disk"""
        logger.info(f"Loading vector store from {self.index_path}")

        # Load FAISS index
        if self.faiss_index_path.exists():
            self.faiss_index = faiss.read_index(str(self.faiss_index_path))
            logger.info(f"Loaded FAISS index from {self.faiss_index_path}")
        else:
            raise FileNotFoundError(f"FAISS index not found at {self.faiss_index_path}")

        # Load documents
        if self.documents_path.exists():
            with open(self.documents_path, 'rb') as f:
                self.documents = pickle.load(f)
            logger.info(f"Loaded {len(self.documents)} documents from {self.documents_path}")
        else:
            raise FileNotFoundError(f"Documents file not found at {self.documents_path}")

        # Load BM25 index
        if self.bm25_path.exists():
            with open(self.bm25_path, 'rb') as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.tokenized_corpus = data["tokenized_corpus"]
            logger.info(f"Loaded BM25 index from {self.bm25_path}")
        else:
            logger.warning(f"BM25 index not found at {self.bm25_path}, rebuilding")
            self.tokenized_corpus = [self._tokenize_text(doc.content) for doc in self.documents]
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "total_documents": len(self.documents),
            "embedding_model": self.embedding_model_name,
            "embedding_dim": self.embedding_dim,
            "faiss_index_size": self.faiss_index.ntotal if self.faiss_index else 0,
            "bm25_initialized": self.bm25 is not None,
            "index_path": str(self.index_path)
        }
