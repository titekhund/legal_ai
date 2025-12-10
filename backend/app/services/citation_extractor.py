"""
Citation extraction and validation service for Georgian legal citations
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.core import get_logger, get_settings
from app.models.schemas import Citation

logger = get_logger(__name__)


class CitationExtractor:
    """
    Service for extracting and validating Georgian legal citations

    Supports multiple citation formats from Georgian Tax Code:
    - მუხლი 168
    - 168-ე მუხლი
    - მუხლი 168, ნაწილი 1
    - მუხლი 168.1.ა
    - მუხლები 168-170
    """

    # Georgian legal citation patterns
    PATTERNS = [
        # Pattern 1: "მუხლი 168.1.ა" - Full dotted notation
        (
            r'მუხლი\s*(\d+)\.(\d+)\.([ა-ჰ])',
            lambda m: {
                "article": m.group(1),
                "clause": m.group(2),
                "letter": m.group(3),
                "raw": m.group(0)
            }
        ),
        # Pattern 2: "მუხლი 168.1" - Article with clause
        (
            r'მუხლი\s*(\d+)\.(\d+)',
            lambda m: {
                "article": m.group(1),
                "clause": m.group(2),
                "letter": None,
                "raw": m.group(0)
            }
        ),
        # Pattern 3: "მუხლი 168, ნაწილი 1, პუნქტი ა" - Full verbose
        (
            r'მუხლი\s*(\d+),?\s*ნაწილი\s*(\d+)(?:,?\s*პუნქტი\s*([ა-ჰ]))?',
            lambda m: {
                "article": m.group(1),
                "clause": m.group(2),
                "letter": m.group(3),
                "raw": m.group(0)
            }
        ),
        # Pattern 4: "168-ე მუხლი" or "168-ე მუხლის" - Ordinal form
        (
            r'(\d+)-ე\s*მუხლ[ი|ის]',
            lambda m: {
                "article": m.group(1),
                "clause": None,
                "letter": None,
                "raw": m.group(0)
            }
        ),
        # Pattern 5: "მუხლი 168" - Simple article reference
        (
            r'მუხლი\s*(\d+)(?![.\d-])',
            lambda m: {
                "article": m.group(1),
                "clause": None,
                "letter": None,
                "raw": m.group(0)
            }
        ),
        # Pattern 6: "მუხლები 168-170" - Article range
        (
            r'მუხლ(?:ებ)?ი\s*(\d+)[-–](\d+)',
            lambda m: {
                "article": f"{m.group(1)}-{m.group(2)}",
                "clause": None,
                "letter": None,
                "raw": m.group(0),
                "is_range": True
            }
        ),
    ]

    # Base URL for matsne.gov.ge (Georgian legislative database)
    MATSNE_BASE_URL = "https://matsne.gov.ge/ka/document/view/1043717"

    def __init__(self, article_index_path: Optional[str] = None):
        """
        Initialize CitationExtractor

        Args:
            article_index_path: Optional path to article index JSON file
        """
        settings = get_settings()

        # Load article index
        if article_index_path:
            self.index_path = Path(article_index_path)
        else:
            # Default path
            tax_code_dir = Path(settings.tax_code_path).parent
            self.index_path = tax_code_dir / "article_index.json"

        self.article_index: Dict[str, any] = {}
        self.valid_articles: Set[str] = set()
        self._load_article_index()

        logger.info(f"CitationExtractor initialized with {len(self.valid_articles)} valid articles")

    def _load_article_index(self) -> None:
        """Load article index from JSON file"""
        try:
            if not self.index_path.exists():
                logger.warning(f"Article index not found at {self.index_path}")
                return

            with open(self.index_path, 'r', encoding='utf-8') as f:
                self.article_index = json.load(f)

            # Create set of valid article numbers for fast lookup
            self.valid_articles = set(self.article_index.get("articles", []))

            logger.info(
                f"Loaded article index with {len(self.valid_articles)} articles "
                f"(max: {self.article_index.get('max_article', 'unknown')})"
            )

        except Exception as e:
            logger.error(f"Failed to load article index: {e}")
            self.valid_articles = set()

    def extract_citations(self, text: str) -> List[Citation]:
        """
        Extract all citations from text

        Args:
            text: Text to extract citations from

        Returns:
            List of Citation objects with validation and enrichment
        """
        citations = []
        seen_citations = set()  # Deduplicate

        # Try each pattern
        for pattern, extractor in self.PATTERNS:
            for match in re.finditer(pattern, text):
                try:
                    # Extract citation components
                    citation_data = extractor(match)

                    # Check if it's a range
                    if citation_data.get("is_range", False):
                        # For ranges, we'll validate the range bounds
                        article_range = citation_data["article"]
                        parts = article_range.split("-")
                        if len(parts) == 2:
                            start_valid = parts[0] in self.valid_articles
                            end_valid = parts[1] in self.valid_articles
                            is_valid = start_valid and end_valid
                        else:
                            is_valid = False
                    else:
                        # Normal single article validation
                        is_valid = self._validate_article_number(
                            citation_data["article"]
                        )

                    # Create normalized key for deduplication
                    citation_key = (
                        citation_data["article"],
                        citation_data.get("clause"),
                        citation_data.get("letter")
                    )

                    if citation_key not in seen_citations:
                        seen_citations.add(citation_key)

                        # Create Citation object
                        citation = Citation(
                            raw_text=citation_data["raw"],
                            article=citation_data["article"],
                            clause=citation_data.get("clause"),
                            letter=citation_data.get("letter"),
                            is_valid=is_valid,
                            matsne_url=self.format_citation_link(
                                citation_data["article"],
                                citation_data.get("clause"),
                                citation_data.get("letter")
                            ) if is_valid else None
                        )

                        citations.append(citation)

                except Exception as e:
                    logger.warning(f"Error extracting citation from match: {e}")
                    continue

        logger.info(f"Extracted {len(citations)} unique citations from text")

        # Log invalid citations for monitoring potential hallucinations
        invalid_citations = [c for c in citations if not c.is_valid]
        if invalid_citations:
            logger.warning(
                f"Found {len(invalid_citations)} potentially invalid citations: "
                f"{[c.article for c in invalid_citations]}"
            )

        return citations

    def validate_citation(
        self,
        citation: Citation,
        tax_code_structure: Optional[Dict] = None
    ) -> bool:
        """
        Validate a citation against the article index

        Args:
            citation: Citation object to validate
            tax_code_structure: Optional detailed structure (not used yet)

        Returns:
            True if citation is valid
        """
        # For now, just check if article number is in the index
        # In the future, could validate clause and letter as well

        # Handle ranges
        if "-" in citation.article:
            parts = citation.article.split("-")
            if len(parts) == 2:
                start_valid = parts[0] in self.valid_articles
                end_valid = parts[1] in self.valid_articles
                return start_valid and end_valid
            return False

        return self._validate_article_number(citation.article)

    def _validate_article_number(self, article: str) -> bool:
        """
        Check if article number exists in index

        Args:
            article: Article number string

        Returns:
            True if valid
        """
        return article in self.valid_articles

    def format_citation_link(
        self,
        article: str,
        clause: Optional[str] = None,
        letter: Optional[str] = None
    ) -> str:
        """
        Format a link to matsne.gov.ge for the citation

        Args:
            article: Article number
            clause: Optional clause/part number
            letter: Optional letter designation

        Returns:
            URL string to matsne.gov.ge
        """
        # Base URL points to the Tax Code document
        url = self.MATSNE_BASE_URL

        # Add article anchor if available
        # Note: The actual anchor format on matsne.gov.ge may vary
        # This is a simplified version
        if article:
            # matsne.gov.ge uses anchors like #ARTICLE_168
            url += f"#ARTICLE_{article}"

            if clause:
                url += f"_{clause}"

            if letter:
                url += f"_{letter}"

        return url

    def get_citation_summary(self, citations: List[Citation]) -> Dict[str, any]:
        """
        Get summary statistics about citations

        Args:
            citations: List of citations

        Returns:
            Dictionary with summary stats
        """
        total = len(citations)
        valid = sum(1 for c in citations if c.is_valid)
        invalid = total - valid

        articles = set(c.article for c in citations)
        with_clauses = sum(1 for c in citations if c.clause)
        with_letters = sum(1 for c in citations if c.letter)

        return {
            "total_citations": total,
            "valid_citations": valid,
            "invalid_citations": invalid,
            "unique_articles": len(articles),
            "citations_with_clauses": with_clauses,
            "citations_with_letters": with_letters,
            "validation_rate": valid / total if total > 0 else 0.0
        }

    def reload_index(self) -> bool:
        """
        Reload the article index from disk

        Returns:
            True if successful
        """
        try:
            self._load_article_index()
            return True
        except Exception as e:
            logger.error(f"Failed to reload article index: {e}")
            return False
