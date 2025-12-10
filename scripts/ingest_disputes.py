#!/usr/bin/env python3
"""
Dispute Data Ingestion Pipeline

Processes Ministry of Finance dispute decisions from various formats
and prepares them for vector search.

Usage:
    python scripts/ingest_disputes.py --input-dir data/raw --output-dir data/processed
    python scripts/ingest_disputes.py --rebuild-index
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from tqdm import tqdm
import pypdf


@dataclass
class Document:
    """Represents a chunked document with metadata."""
    text: str
    metadata: Dict[str, Any]
    chunk_id: int = 0


class LegalChunker:
    """
    Chunks legal documents while preserving structure.

    Designed specifically for Georgian tax dispute decisions
    from the Ministry of Finance.
    """

    # Georgian dispute document structure markers
    STRUCTURE_MARKERS = [
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

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        preserve_structure: bool = True
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
            preserve_structure: Whether to preserve document structure markers
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_structure = preserve_structure

    def chunk_document(self, text: str, metadata: dict) -> List[Document]:
        """
        Split document into chunks while preserving structure.

        Args:
            text: Full document text
            metadata: Document metadata (doc_id, date, category, etc.)

        Returns:
            List of Document objects with chunks and metadata
        """
        if self.preserve_structure:
            return self._chunk_with_structure(text, metadata)
        else:
            return self._chunk_simple(text, metadata)

    def _chunk_with_structure(self, text: str, metadata: dict) -> List[Document]:
        """Chunk while preserving legal document structure."""
        chunks = []

        # Split by structure markers
        sections = self._split_by_markers(text)

        current_chunk = ""
        chunk_id = 0

        for section_marker, section_text in sections:
            # If adding this section exceeds chunk size, save current chunk
            if len(current_chunk) + len(section_text) > self.chunk_size and current_chunk:
                chunks.append(Document(
                    text=current_chunk.strip(),
                    metadata={**metadata, "section": section_marker},
                    chunk_id=chunk_id
                ))
                chunk_id += 1

                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + section_marker + section_text
                else:
                    current_chunk = section_marker + section_text
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += section_marker + section_text

        # Add final chunk
        if current_chunk.strip():
            chunks.append(Document(
                text=current_chunk.strip(),
                metadata={**metadata, "section": "final"},
                chunk_id=chunk_id
            ))

        return chunks

    def _split_by_markers(self, text: str) -> List[tuple[str, str]]:
        """Split text by structure markers."""
        sections = []
        current_pos = 0

        # Find all marker positions
        marker_positions = []
        for marker in self.STRUCTURE_MARKERS:
            for match in re.finditer(re.escape(marker), text):
                marker_positions.append((match.start(), marker))

        # Sort by position
        marker_positions.sort()

        # Extract sections
        for i, (pos, marker) in enumerate(marker_positions):
            if i > 0:
                # Save previous section
                prev_pos, prev_marker = marker_positions[i-1]
                section_text = text[prev_pos + len(prev_marker):pos].strip()
                sections.append((prev_marker, section_text))

            # Handle last section
            if i == len(marker_positions) - 1:
                section_text = text[pos + len(marker):].strip()
                sections.append((marker, section_text))

        # If no markers found, return entire text
        if not sections:
            sections.append(("", text))

        return sections

    def _chunk_simple(self, text: str, metadata: dict) -> List[Document]:
        """Simple chunking without structure preservation."""
        chunks = []
        chunk_id = 0

        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            if chunk_text.strip():
                chunks.append(Document(
                    text=chunk_text.strip(),
                    metadata=metadata,
                    chunk_id=chunk_id
                ))
                chunk_id += 1

        return chunks


def extract_case_metadata(text: str) -> Dict[str, Any]:
    """
    Extract metadata from Georgian dispute decision document.

    Args:
        text: Full document text

    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        "doc_number": None,
        "date": None,
        "category": None,
        "assessing_body": None,
        "legislative_norms": [],
        "dispute_subject": None,
        "appealed_decision": None,
        "assessed_amounts": {},
        "final_decision": None,
    }

    # Extract document number
    doc_num_pattern = r"დოკუმენტის #\s*[:：]?\s*([А-Яа-я0-9\-\/]+)"
    match = re.search(doc_num_pattern, text)
    if match:
        metadata["doc_number"] = match.group(1).strip()

    # Extract date
    date_pattern = r"მიღების თარიღი:\s*(\d{1,2}\.\d{1,2}\.\d{4})"
    match = re.search(date_pattern, text)
    if match:
        metadata["date"] = match.group(1).strip()

    # Extract category
    category_pattern = r"კატეგორია:\s*([^\n]+)"
    match = re.search(category_pattern, text)
    if match:
        metadata["category"] = match.group(1).strip()

    # Extract assessing body
    body_pattern = r"დამრიცხველი ორგანო:\s*([^\n]+)"
    match = re.search(body_pattern, text)
    if match:
        metadata["assessing_body"] = match.group(1).strip()

    # Extract legislative norms (articles)
    norms_pattern = r"საკანონმდებლო ნორმები:\s*([^\n]+)"
    match = re.search(norms_pattern, text)
    if match:
        norms_text = match.group(1).strip()
        # Extract article numbers (e.g., "მუხლი 82", "მუხლი 165-166")
        articles = re.findall(r"მუხლი\s*(\d+(?:\-\d+)?)", norms_text)
        metadata["legislative_norms"] = articles

    # Extract dispute subject
    subject_pattern = r"დავის საგანი:\s*([^\n]+(?:\n(?![\w\s]+:)[^\n]+)*)"
    match = re.search(subject_pattern, text)
    if match:
        metadata["dispute_subject"] = match.group(1).strip()

    # Extract final decision
    decision_pattern = r"საბოლოო გადაწყვეტილება:\s*([^\n]+)"
    match = re.search(decision_pattern, text)
    if match:
        decision_text = match.group(1).strip()
        metadata["final_decision"] = decision_text

        # Parse decision type
        if "დაკმაყოფილდა" in decision_text.lower():
            metadata["decision_type"] = "satisfied"
        elif "არ დაკმაყოფილდა" in decision_text.lower():
            metadata["decision_type"] = "rejected"
        elif "ნაწილობრივ" in decision_text.lower():
            metadata["decision_type"] = "partially_satisfied"
        else:
            metadata["decision_type"] = "other"

    return metadata


def load_pdf(file_path: Path) -> str:
    """Load text from PDF file."""
    try:
        reader = pypdf.PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to load PDF {file_path}: {e}")


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load structured case data from JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load JSON {file_path}: {e}")


def load_text(file_path: Path) -> str:
    """Load plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to load text {file_path}: {e}")


def process_file(
    file_path: Path,
    chunker: LegalChunker,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Process a single dispute document file.

    Args:
        file_path: Path to input file
        chunker: LegalChunker instance
        output_dir: Directory for processed output

    Returns:
        Processing result with status and metadata
    """
    result = {
        "file": str(file_path),
        "status": "success",
        "chunks": 0,
        "error": None
    }

    try:
        # Load file based on extension
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            text = load_pdf(file_path)
            metadata = extract_case_metadata(text)
        elif suffix == '.json':
            data = load_json(file_path)
            text = data.get('text', '')
            metadata = data.get('metadata', extract_case_metadata(text))
        elif suffix in ['.txt', '.text']:
            text = load_text(file_path)
            metadata = extract_case_metadata(text)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        # Add source file to metadata
        metadata['source_file'] = str(file_path.name)
        metadata['processed_at'] = datetime.now().isoformat()

        # Chunk document
        chunks = chunker.chunk_document(text, metadata)
        result["chunks"] = len(chunks)

        # Save processed chunks
        output_file = output_dir / f"{file_path.stem}_processed.json"
        chunks_data = [
            {
                "text": chunk.text,
                "metadata": chunk.metadata,
                "chunk_id": chunk.chunk_id
            }
            for chunk in chunks
        ]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "source": str(file_path.name),
                "metadata": metadata,
                "chunks": chunks_data
            }, f, ensure_ascii=False, indent=2)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def ingest_disputes(
    input_dir: Path,
    output_dir: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    preserve_structure: bool = True
) -> Dict[str, Any]:
    """
    Main ingestion pipeline.

    Args:
        input_dir: Directory containing raw dispute documents
        output_dir: Directory for processed output
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks
        preserve_structure: Whether to preserve document structure

    Returns:
        Ingestion report with statistics
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize chunker
    chunker = LegalChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        preserve_structure=preserve_structure
    )

    # Find all supported files
    supported_extensions = ['.pdf', '.json', '.txt', '.text']
    files = []
    for ext in supported_extensions:
        files.extend(input_dir.glob(f"*{ext}"))

    if not files:
        print(f"⚠️  No supported files found in {input_dir}")
        return {"status": "no_files", "processed": 0, "errors": 0}

    # Process files with progress bar
    results = []
    total_chunks = 0
    errors = 0

    print(f"📂 Processing {len(files)} files from {input_dir}")

    for file_path in tqdm(files, desc="Ingesting documents"):
        result = process_file(file_path, chunker, output_dir)
        results.append(result)

        if result["status"] == "success":
            total_chunks += result["chunks"]
        else:
            errors += 1
            print(f"\n❌ Error processing {file_path.name}: {result['error']}")

    # Generate report
    report = {
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "total_files": len(files),
        "processed": len(files) - errors,
        "errors": errors,
        "total_chunks": total_chunks,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "preserve_structure": preserve_structure,
        "results": results
    }

    # Save report
    report_file = output_dir / f"ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Ingestion complete!")
    print(f"   Files processed: {report['processed']}/{report['total_files']}")
    print(f"   Total chunks: {total_chunks}")
    print(f"   Errors: {errors}")
    print(f"   Report saved to: {report_file}")

    return report


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest and process Ministry of Finance dispute decisions"
    )

    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('data/raw'),
        help='Directory containing raw dispute documents (default: data/raw)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/processed'),
        help='Directory for processed output (default: data/processed)'
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Target chunk size in characters (default: 1000)'
    )

    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Overlap between chunks in characters (default: 200)'
    )

    parser.add_argument(
        '--no-preserve-structure',
        action='store_true',
        help='Disable structure preservation (use simple chunking)'
    )

    parser.add_argument(
        '--rebuild-index',
        action='store_true',
        help='Rebuild vector and BM25 indices from processed data'
    )

    args = parser.parse_args()

    if args.rebuild_index:
        print("🔄 Rebuilding indices...")
        print("⚠️  Index rebuilding requires vector_store.py integration")
        print("   This feature will be implemented when connecting to VectorStore")
        return 0

    # Validate input directory
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        print(f"   Creating directory structure...")
        args.input_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Please add dispute documents to {args.input_dir} and run again")
        return 1

    # Run ingestion
    try:
        report = ingest_disputes(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            preserve_structure=not args.no_preserve_structure
        )

        return 0 if report["errors"] == 0 else 1

    except Exception as e:
        print(f"❌ Fatal error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
