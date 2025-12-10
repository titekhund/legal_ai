"""
Tests for dispute data ingestion pipeline.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from ingest_disputes import LegalChunker, Document, extract_case_metadata


def test_legal_chunker_initialization():
    """Test LegalChunker can be initialized with default parameters."""
    chunker = LegalChunker()
    assert chunker.chunk_size == 1000
    assert chunker.chunk_overlap == 200
    assert chunker.preserve_structure is True


def test_legal_chunker_custom_params():
    """Test LegalChunker with custom parameters."""
    chunker = LegalChunker(
        chunk_size=500,
        chunk_overlap=100,
        preserve_structure=False
    )
    assert chunker.chunk_size == 500
    assert chunker.chunk_overlap == 100
    assert chunker.preserve_structure is False


def test_structure_markers():
    """Test that structure markers are defined correctly."""
    chunker = LegalChunker()
    expected_markers = [
        "დოკუმენტის #",
        "მიღების თარიღი:",
        "კატეგორია:",
        "დამრიცხველი ორგანო:",
        "საკანონმდებლო ნორმები:",
        "დავის საგანი:",
        "გასაჩივრებული გადაწყვეტილება:",
        "დარიცხული თანხები:",
        "პროცედურული გარემოებები:",
        "სადავო საკითხი",
        "ფაქტები:",
        "შემოსავლების სამსახურის პოზიცია:",
        "მომჩივნის არგუმენტები:",
        "საბჭოს დასკვნა:",
        "საბოლოო გადაწყვეტილება:",
        "გასაჩივრების ვადა:",
    ]
    assert chunker.STRUCTURE_MARKERS == expected_markers


def test_simple_chunking():
    """Test simple chunking without structure preservation."""
    chunker = LegalChunker(
        chunk_size=50,
        chunk_overlap=10,
        preserve_structure=False
    )

    text = "This is a test document. " * 10  # 250 characters
    metadata = {"doc_id": "test_001"}

    chunks = chunker.chunk_document(text, metadata)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)
    assert all(chunk.metadata["doc_id"] == "test_001" for chunk in chunks)


def test_extract_case_metadata_document_number():
    """Test extraction of document number from Georgian text."""
    text = """
    დოკუმენტის # ТД-2024-123
    მიღების თარიღი: 15.01.2024
    კატეგორია: დღგ
    """

    metadata = extract_case_metadata(text)
    assert metadata["doc_number"] == "ТД-2024-123"
    assert metadata["date"] == "15.01.2024"
    assert metadata["category"] == "დღგ"


def test_extract_case_metadata_legislative_norms():
    """Test extraction of legislative norms (articles)."""
    text = """
    საკანონმდებლო ნორმები: საგადასახადო კოდექსის მუხლი 82, მუხლი 165-166
    """

    metadata = extract_case_metadata(text)
    assert "82" in metadata["legislative_norms"]
    assert "165-166" in metadata["legislative_norms"]


def test_extract_case_metadata_final_decision_satisfied():
    """Test extraction of final decision - satisfied."""
    text = """
    საბოლოო გადაწყვეტილება: საჩივარი დაკმაყოფილდა
    """

    metadata = extract_case_metadata(text)
    assert metadata["final_decision"] == "საჩივარი დაკმაყოფილდა"
    assert metadata["decision_type"] == "satisfied"


def test_extract_case_metadata_final_decision_rejected():
    """Test extraction of final decision - rejected."""
    text = """
    საბოლოო გადაწყვეტილება: საჩივარი არ დაკმაყოფილდა
    """

    metadata = extract_case_metadata(text)
    assert metadata["final_decision"] == "საჩივარი არ დაკმაყოფილდა"
    assert metadata["decision_type"] == "rejected"


def test_extract_case_metadata_final_decision_partial():
    """Test extraction of final decision - partially satisfied."""
    text = """
    საბოლოო გადაწყვეტილება: საჩივარი ნაწილობრივ დაკმაყოფილდა
    """

    metadata = extract_case_metadata(text)
    assert metadata["decision_type"] == "partially_satisfied"


def test_extract_case_metadata_complete_document():
    """Test extraction from a complete Georgian dispute document."""
    text = """
    დოკუმენტის # ТД-2024-456
    მიღების თარიღი: 20.03.2024
    კატეგორია: საშემოსავლო გადასახადი
    დამრიცხველი ორგანო: შ.პ.ს. სამეგრელო-ზემო სვანეთის საგადასახადო ინსპექცია
    საკანონმდებლო ნორმები: საგადასახადო კოდექსის მუხლი 82
    დავის საგანი: ფიზიკური პირის მიერ ქონების რეალიზაციის დაბეგვრა
    გასაჩივრებული გადაწყვეტილება: გადასახადის დარიცხვის შესახებ გადაწყვეტილება

    სადავო საკითხი #1

    ფაქტები:
    მომჩივანმა გაყიდა უძრავი ქონება.

    შემოსავლების სამსახურის პოზიცია:
    გაყიდვა ექვემდებარება დაბეგვრას.

    მომჩივნის არგუმენტები:
    ქონება იყო საკუთრებაში 2 წელზე მეტი.

    საბჭოს დასკვნა:
    საბჭო ეთანხმება მომჩივანს.

    საბოლოო გადაწყვეტილება: საჩივარი დაკმაყოფილდა
    გასაჩივრების ვადა: 30 დღე
    """

    metadata = extract_case_metadata(text)

    assert metadata["doc_number"] == "ТД-2024-456"
    assert metadata["date"] == "20.03.2024"
    assert metadata["category"] == "საშემოსავლო გადასახადი"
    assert metadata["assessing_body"] == "შ.პ.ს. სამეგრელო-ზემო სვანეთის საგადასახადო ინსპექცია"
    assert "82" in metadata["legislative_norms"]
    assert "ფიზიკური პირის მიერ ქონების რეალიზაციის დაბეგვრა" in metadata["dispute_subject"]
    assert metadata["decision_type"] == "satisfied"


def test_chunk_with_structure():
    """Test chunking with Georgian structure preservation."""
    chunker = LegalChunker(
        chunk_size=200,
        chunk_overlap=50,
        preserve_structure=True
    )

    text = """
    დოკუმენტის # ТД-001

    მიღების თარიღი: 01.01.2024

    კატეგორია: დღგ

    ფაქტები:
    ეს არის ფაქტების აღწერა რომელიც შეიძლება იყოს საკმაოდ გრძელი ტექსტი.

    საბჭოს დასკვნა:
    საბჭომ მიიღო გადაწყვეტილება.
    """

    metadata = {"test": "value"}
    chunks = chunker.chunk_document(text, metadata)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)
    # Verify metadata is preserved
    assert all(chunk.metadata["test"] == "value" for chunk in chunks)
