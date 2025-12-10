"""
Template Store for Document Generation

Manages document templates with efficient retrieval and search.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.models.schemas import DocumentTemplate, DocumentType, TemplateVariable

logger = get_logger(__name__)


class TemplateStore:
    """
    Store and manage document templates

    Templates are loaded from JSON files and indexed for efficient
    retrieval by type, language, and search queries.
    """

    def __init__(self, templates_dir: str = "data/templates"):
        """
        Initialize template store

        Args:
            templates_dir: Directory containing template JSON files
        """
        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, DocumentTemplate] = {}
        self.types: Dict[str, DocumentType] = {}
        self._initialized = False

        logger.info(f"Template store initialized with directory: {templates_dir}")

    async def load_templates(self) -> bool:
        """
        Load templates from directory

        Returns:
            True if templates loaded successfully
        """
        try:
            # Ensure templates directory exists
            self.templates_dir.mkdir(parents=True, exist_ok=True)

            # Load document types
            types_file = self.templates_dir / "document_types.json"
            if types_file.exists():
                with open(types_file, "r", encoding="utf-8") as f:
                    types_data = json.load(f)
                    for type_data in types_data:
                        doc_type = DocumentType(**type_data)
                        self.types[doc_type.id] = doc_type
                logger.info(f"Loaded {len(self.types)} document types")
            else:
                logger.warning(f"Document types file not found: {types_file}")
                # Load default types
                self._load_default_types()

            # Load templates
            templates_file = self.templates_dir / "templates.json"
            if templates_file.exists():
                with open(templates_file, "r", encoding="utf-8") as f:
                    templates_data = json.load(f)
                    for template_data in templates_data:
                        template = DocumentTemplate(**template_data)
                        self.templates[template.id] = template
                logger.info(f"Loaded {len(self.templates)} templates")
            else:
                logger.warning(f"Templates file not found: {templates_file}")
                # Load default templates
                self._load_default_templates()

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Error loading templates: {e}", exc_info=True)
            return False

    def _load_default_types(self):
        """Load default document types for initial setup"""
        default_types = [
            DocumentType(
                id="nda",
                name_ka="კონფიდენციალურობის შეთანხმება",
                name_en="Non-Disclosure Agreement",
                description_ka="კონფიდენციალურობის შეთანხმება საქმიანი ინფორმაციის დასაცავად",
                description_en="Agreement to protect confidential business information",
                required_fields=["party1_name", "party2_name", "date", "purpose"],
                optional_fields=["jurisdiction", "duration_months"]
            ),
            DocumentType(
                id="employment_contract",
                name_ka="შრომითი ხელშეკრულება",
                name_en="Employment Contract",
                description_ka="შრომითი ურთიერთობის ოფიციალური ხელშეკრულება",
                description_en="Official employment relationship contract",
                required_fields=["employer_name", "employee_name", "position", "salary", "start_date"],
                optional_fields=["probation_period", "work_schedule", "benefits"]
            ),
            DocumentType(
                id="board_resolution",
                name_ka="დირექტორთა საბჭოს დადგენილება",
                name_en="Board Resolution",
                description_ka="დირექტორთა საბჭოს ოფიციალური გადაწყვეტილება",
                description_en="Official board of directors decision",
                required_fields=["company_name", "resolution_date", "resolution_text"],
                optional_fields=["attendees", "voting_results"]
            )
        ]

        for doc_type in default_types:
            self.types[doc_type.id] = doc_type

        logger.info(f"Loaded {len(default_types)} default document types")

    def _load_default_templates(self):
        """Load default templates for initial setup"""
        # Simple NDA template
        nda_template = DocumentTemplate(
            id="nda_ka_01",
            type="nda",
            name_ka="კონფიდენციალურობის ხელშეკრულება - სტანდარტული",
            name_en="Non-Disclosure Agreement - Standard",
            language="ka",
            content="""# კონფიდენციალურობის შეთანხმება

ეს შეთანხმება დადებულია {{date}}-ში შემდეგ მხარეებს შორის:

**პირველი მხარე:** {{party1_name}}
**მეორე მხარე:** {{party2_name}}

## 1. შეთანხმების საგანი

მხარეები ეთანხმებიან კონფიდენციალური ინფორმაციის გაცვლას შემდეგი მიზნით: {{purpose}}

## 2. კონფიდენციალური ინფორმაცია

კონფიდენციალურ ინფორმაციად ითვლება ყველა ინფორმაცია, რომელიც მიეწოდება ერთი მხარიდან მეორეს და მონიშნულია როგორც "კონფიდენციალური".

## 3. ვალდებულებები

- მხარეები ვალდებული არიან დაიცვან მიღებული ინფორმაციის კონფიდენციალურობა
- კონფიდენციალური ინფორმაცია არ უნდა გაიმჟღავნდეს მესამე პირებისთვის
- ინფორმაცია გამოიყენება მხოლოდ შეთანხმებით განსაზღვრული მიზნით

## 4. შეთანხმების ვადა

ეს შეთანხმება ძალაშია {{duration_months}} თვის განმავლობაში.

## 5. განრიდება პასუხისმგებლობისგან

ვალდებულება არ ვრცელდება ინფორმაციაზე, რომელიც:
- საჯაროდ ხელმისაწვდომი იყო ამ შეთანხმების დადებამდე
- გახდა საჯაროდ ხელმისაწვდომი მხარის ბრალის გარეშე
- კანონით მოითხოვება გამჟღავნება

**პირველი მხარე:**
ხელმოწერა: _________________
თარიღი: _________________

**მეორე მხარე:**
ხელმოწერა: _________________
თარიღი: _________________
""",
            variables=[
                TemplateVariable(
                    name="party1_name",
                    label_ka="პირველი მხარის სახელი",
                    label_en="First Party Name",
                    type="text",
                    required=True,
                    placeholder_ka="მაგ: შპს \"კომპანია\""
                ),
                TemplateVariable(
                    name="party2_name",
                    label_ka="მეორე მხარის სახელი",
                    label_en="Second Party Name",
                    type="text",
                    required=True,
                    placeholder_ka="მაგ: ა/შ \"პარტნიორი\""
                ),
                TemplateVariable(
                    name="date",
                    label_ka="თარიღი",
                    label_en="Date",
                    type="date",
                    required=True
                ),
                TemplateVariable(
                    name="purpose",
                    label_ka="შეთანხმების მიზანი",
                    label_en="Purpose",
                    type="text",
                    required=True,
                    placeholder_ka="მაგ: პოტენციური საქმიანი თანამშრომლობის განხილვა"
                ),
                TemplateVariable(
                    name="duration_months",
                    label_ka="ხანგრძლივობა (თვეები)",
                    label_en="Duration (months)",
                    type="number",
                    required=False,
                    default="12"
                )
            ],
            related_articles=[],
            category="ხელშეკრულებები",
            tags=["კონფიდენციალურობა", "NDA", "ხელშეკრულება"]
        )

        self.templates[nda_template.id] = nda_template
        logger.info("Loaded 1 default template")

    def get_template(self, template_id: str) -> Optional[DocumentTemplate]:
        """
        Get template by ID

        Args:
            template_id: Template identifier

        Returns:
            Template or None if not found
        """
        return self.templates.get(template_id)

    def get_templates_by_type(
        self,
        document_type: str,
        language: Optional[str] = None
    ) -> List[DocumentTemplate]:
        """
        Get all templates for a document type

        Args:
            document_type: Document type ID
            language: Filter by language ('ka' or 'en')

        Returns:
            List of matching templates
        """
        results = [
            template for template in self.templates.values()
            if template.type == document_type
        ]

        if language:
            results = [t for t in results if t.language == language]

        return results

    def search_templates(
        self,
        query: str,
        document_type: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[DocumentTemplate]:
        """
        Search templates by query

        Args:
            query: Search query
            document_type: Filter by document type
            language: Filter by language

        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        results = []

        for template in self.templates.values():
            # Apply filters
            if document_type and template.type != document_type:
                continue
            if language and template.language != language:
                continue

            # Check if query matches
            if (query_lower in template.name_ka.lower() or
                query_lower in template.name_en.lower() or
                any(query_lower in tag.lower() for tag in template.tags) or
                (template.category and query_lower in template.category.lower())):
                results.append(template)

        return results

    def get_document_type(self, type_id: str) -> Optional[DocumentType]:
        """
        Get document type by ID

        Args:
            type_id: Document type ID

        Returns:
            DocumentType or None if not found
        """
        return self.types.get(type_id)

    def list_document_types(self) -> List[DocumentType]:
        """
        List all available document types

        Returns:
            List of document types
        """
        return list(self.types.values())

    def get_status(self) -> dict:
        """
        Get template store status

        Returns:
            Status dictionary
        """
        return {
            "initialized": self._initialized,
            "templates_count": len(self.templates),
            "types_count": len(self.types),
            "templates_dir": str(self.templates_dir),
            "templates_by_language": {
                "ka": len([t for t in self.templates.values() if t.language == "ka"]),
                "en": len([t for t in self.templates.values() if t.language == "en"])
            }
        }
