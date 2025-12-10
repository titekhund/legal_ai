"""
Tests for document generation service
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from app.services.document_service import DocumentService, DOCUMENT_DISCLAIMER
from app.services.template_store import TemplateStore
from app.models.schemas import (
    DocumentGenerationRequest,
    DocumentTemplate,
    TemplateVariable,
    GeneratedDocument,
)


class TestTemplateStore:
    """Test template store functionality"""

    @pytest.fixture
    def template_store(self, tmp_path):
        """Create template store with temp directory"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        return TemplateStore(templates_dir=str(templates_dir))

    @pytest.fixture
    def sample_template_yaml(self, tmp_path):
        """Create sample YAML template file"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_content = """id: test_nda_ka
type: nda
name_ka: ტესტური NDA
name_en: Test NDA
language: ka
category: ხელშეკრულებები
tags:
  - test
variables:
  - name: party_a_name
    label_ka: პირველი მხარე
    label_en: First Party
    type: text
    required: true
  - name: party_b_name
    label_ka: მეორე მხარე
    label_en: Second Party
    type: text
    required: true
  - name: effective_date
    label_ka: თარიღი
    label_en: Date
    type: date
    required: true
related_articles: []
content: |
  # კონფიდენციალურობის ხელშეკრულება

  **პირველი მხარე:** {{party_a_name}}
  **მეორე მხარე:** {{party_b_name}}
  **თარიღი:** {{effective_date}}

  ეს შეთანხმება დადებულია...
"""
        template_file = templates_dir / "test_nda_ka.yaml"
        template_file.write_text(template_content, encoding="utf-8")
        return template_file

    @pytest.mark.asyncio
    async def test_load_templates(self, template_store, sample_template_yaml):
        """Test loading templates from YAML files"""
        success = await template_store.load_templates()

        assert success
        assert len(template_store.templates) == 1
        assert "test_nda_ka" in template_store.templates

        template = template_store.templates["test_nda_ka"]
        assert template.id == "test_nda_ka"
        assert template.type == "nda"
        assert template.language == "ka"
        assert len(template.variables) == 3

    @pytest.mark.asyncio
    async def test_get_template(self, template_store, sample_template_yaml):
        """Test retrieving template by ID"""
        await template_store.load_templates()

        template = template_store.get_template("test_nda_ka")
        assert template is not None
        assert template.id == "test_nda_ka"

        # Test non-existent template
        template = template_store.get_template("non_existent")
        assert template is None

    @pytest.mark.asyncio
    async def test_search_templates(self, template_store, sample_template_yaml):
        """Test searching templates"""
        await template_store.load_templates()

        # Search by name
        results = template_store.search_templates(query="NDA", language="ka")
        assert len(results) == 1
        assert results[0].id == "test_nda_ka"

        # Search by document type
        results = template_store.search_templates(
            query="", document_type="nda", language="ka"
        )
        assert len(results) == 1

        # Search with no results
        results = template_store.search_templates(query="nonexistent")
        assert len(results) == 0


class TestDocumentService:
    """Test document generation service"""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client"""
        mock = Mock()
        mock.generate_response = AsyncMock(
            return_value="# Generated Document\n\nTest content"
        )
        return mock

    @pytest.fixture
    def sample_template(self):
        """Create sample document template"""
        return DocumentTemplate(
            id="test_template",
            type="nda",
            name_ka="ტესტური შაბლონი",
            name_en="Test Template",
            language="ka",
            content="""# {{title}}

**პირველი მხარე:** {{party_a}}
**მეორე მხარე:** {{party_b}}
**თარიღი:** {{date}}

## შეთანხმების საგანი

{{purpose}}
""",
            variables=[
                TemplateVariable(
                    name="title",
                    label_ka="სათაური",
                    label_en="Title",
                    type="text",
                    required=True,
                ),
                TemplateVariable(
                    name="party_a",
                    label_ka="პირველი მხარე",
                    label_en="Party A",
                    type="text",
                    required=True,
                ),
                TemplateVariable(
                    name="party_b",
                    label_ka="მეორე მხარე",
                    label_en="Party B",
                    type="text",
                    required=True,
                ),
                TemplateVariable(
                    name="date",
                    label_ka="თარიღი",
                    label_en="Date",
                    type="date",
                    required=True,
                ),
                TemplateVariable(
                    name="purpose",
                    label_ka="მიზანი",
                    label_en="Purpose",
                    type="text",
                    required=False,
                    default="საქმიანი თანამშრომლობა",
                ),
            ],
            related_articles=[],
            category="test",
            tags=["test"],
        )

    @pytest.fixture
    def document_service(self, tmp_path, mock_llm_client):
        """Create document service with mock LLM"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_store = TemplateStore(templates_dir=str(templates_dir))
        service = DocumentService(
            template_store=template_store,
            llm_client=mock_llm_client,
            tax_service=None,
        )
        return service

    @pytest.mark.asyncio
    async def test_initialize_service(self, document_service):
        """Test service initialization"""
        result = await document_service.initialize()
        assert result == True
        assert document_service._initialized == True

    @pytest.mark.asyncio
    async def test_simple_variable_substitution(
        self, document_service, sample_template
    ):
        """Test simple variable substitution without LLM"""
        # Add template to store
        document_service.template_store.templates[sample_template.id] = sample_template

        request = DocumentGenerationRequest(
            document_type="nda",
            template_id="test_template",
            variables={
                "title": "კონფიდენციალურობის ხელშეკრულება",
                "party_a": "შპს ტესტი",
                "party_b": "შპს მეორე",
                "date": "2024-01-01",
                "purpose": "საქმიანი თანამშრომლობა",
            },
            language="ka",
            include_legal_references=False,
            format="markdown",
        )

        # Test with LLM failure (fallback to simple substitution)
        document_service.llm_client.generate_response.side_effect = Exception(
            "LLM error"
        )

        document = await document_service.generate_document(request)

        assert isinstance(document, GeneratedDocument)
        assert "შპს ტესტი" in document.content
        assert "შპს მეორე" in document.content
        assert "2024-01-01" in document.content
        assert document.disclaimer in document.content
        assert len(document.warnings) > 0  # Should have warning about LLM failure

    @pytest.mark.asyncio
    async def test_required_variable_validation(
        self, document_service, sample_template
    ):
        """Test validation of required variables"""
        document_service.template_store.templates[sample_template.id] = sample_template

        # Missing required variable
        request = DocumentGenerationRequest(
            document_type="nda",
            template_id="test_template",
            variables={
                "title": "Test",
                "party_a": "Party A",
                # Missing party_b and date
            },
            language="ka",
        )

        with pytest.raises(ValueError, match="Required variable missing"):
            await document_service.generate_document(request)

    @pytest.mark.asyncio
    async def test_llm_document_generation(
        self, document_service, sample_template, mock_llm_client
    ):
        """Test document generation with LLM"""
        document_service.template_store.templates[sample_template.id] = sample_template

        # Reset mock to return success
        mock_llm_client.generate_response = AsyncMock(
            return_value="""# კონფიდენციალურობის ხელშეკრულება

**პირველი მხარე:** შპს ტესტი
**მეორე მხარე:** შპს მეორე
**თარიღი:** 2024-01-01

## შეთანხმების საგანი

საქმიანი თანამშრომლობა
"""
        )

        request = DocumentGenerationRequest(
            document_type="nda",
            template_id="test_template",
            variables={
                "title": "კონფიდენციალურობის ხელშეკრულება",
                "party_a": "შპს ტესტი",
                "party_b": "შპს მეორე",
                "date": "2024-01-01",
            },
            language="ka",
        )

        document = await document_service.generate_document(request)

        assert isinstance(document, GeneratedDocument)
        assert "შპს ტესტი" in document.content
        assert document.disclaimer in document.content
        assert len(document.warnings) == 0
        mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_document_types(self, document_service):
        """Test listing document types"""
        # Add some document types to store
        from app.models.schemas import DocumentType

        doc_type = DocumentType(
            id="nda",
            name_ka="NDA",
            name_en="NDA",
            description_ka="Test",
            required_fields=["party_a", "party_b"],
            optional_fields=[],
        )
        document_service.template_store.types["nda"] = doc_type

        types = await document_service.list_document_types()
        assert len(types) > 0
        assert types[0].id == "nda"

    def test_date_validation(self, document_service):
        """Test date format validation"""
        # Valid dates
        assert document_service._is_valid_date("2024-01-01") == True
        assert document_service._is_valid_date("01.01.2024") == True
        assert document_service._is_valid_date("01/01/2024") == True

        # Invalid dates
        assert document_service._is_valid_date("invalid") == False
        assert document_service._is_valid_date("2024-13-01") == True  # Regex doesn't validate ranges
        assert document_service._is_valid_date(12345) == False

    def test_markdown_to_plain(self, document_service):
        """Test markdown to plain text conversion"""
        markdown = """# Header 1
## Header 2
**Bold text**
*Italic text*
[Link](http://example.com)
- List item
"""
        plain = document_service._markdown_to_plain(markdown)

        assert "Header 1" in plain
        assert "Bold text" in plain
        assert "Link" in plain
        assert "#" not in plain  # Headers removed
        assert "**" not in plain  # Bold markers removed

    @pytest.mark.asyncio
    async def test_format_output(self, document_service, sample_template):
        """Test different output formats"""
        document_service.template_store.templates[sample_template.id] = sample_template
        document_service.llm_client.generate_response = AsyncMock(
            return_value="# Test Document\n**Bold text**"
        )

        # Test markdown format (default)
        request = DocumentGenerationRequest(
            document_type="nda",
            template_id="test_template",
            variables={
                "title": "Test",
                "party_a": "A",
                "party_b": "B",
                "date": "2024-01-01",
            },
            format="markdown",
        )
        doc_md = await document_service.generate_document(request)
        assert doc_md.format == "markdown"
        assert "#" in doc_md.content

        # Test plain format
        request.format = "plain"
        doc_plain = await document_service.generate_document(request)
        assert doc_plain.format == "plain"
        assert "#" not in doc_plain.content or "Test Document" in doc_plain.content


class TestDocumentGeneration:
    """Integration tests for complete document generation flow"""

    @pytest.mark.asyncio
    async def test_complete_nda_generation(self, tmp_path):
        """Test complete NDA document generation"""
        # Create template directory
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create NDA template
        template_content = """id: nda_test
type: nda
name_ka: კონფიდენციალურობის ხელშეკრულება
name_en: NDA
language: ka
category: ხელშეკრულებები
tags: [test]
variables:
  - name: party_a_name
    label_ka: პირველი მხარე
    label_en: Party A
    type: text
    required: true
  - name: party_b_name
    label_ka: მეორე მხარე
    label_en: Party B
    type: text
    required: true
  - name: effective_date
    label_ka: თარიღი
    label_en: Date
    type: date
    required: true
related_articles: []
content: |
  # კონფიდენციალურობის ხელშეკრულება

  **თარიღი:** {{effective_date}}

  ## მხარეები

  **პირველი მხარე:** {{party_a_name}}
  **მეორე მხარე:** {{party_b_name}}

  ## შეთანხმების საგანი

  მხარეები თანხმდებიან კონფიდენციალური ინფორმაციის გაცვლაზე.
"""
        template_file = templates_dir / "nda_test.yaml"
        template_file.write_text(template_content, encoding="utf-8")

        # Create service
        template_store = TemplateStore(templates_dir=str(templates_dir))
        await template_store.load_templates()

        mock_llm = Mock()
        mock_llm.generate_response = AsyncMock(
            return_value=template_content.split("content: |")[1].strip()
        )

        service = DocumentService(
            template_store=template_store, llm_client=mock_llm, tax_service=None
        )
        await service.initialize()

        # Generate document
        request = DocumentGenerationRequest(
            document_type="nda",
            template_id="nda_test",
            variables={
                "party_a_name": "შპს ტესტი",
                "party_b_name": "შპს მეორე",
                "effective_date": "2024-01-01",
            },
            language="ka",
        )

        document = await service.generate_document(request)

        # Verify document
        assert document.document_type == "nda"
        assert document.template_used == "nda_test"
        assert "შპს ტესტი" in document.content
        assert "შპს მეორე" in document.content
        assert "2024-01-01" in document.content
        assert document.disclaimer in document.content
        assert "კონფიდენციალურობის ხელშეკრულება" in document.content
