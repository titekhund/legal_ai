"""
Document Generation API endpoints
"""
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core import get_logger
from app.models import (
    DocumentGenerationRequest,
    DocumentTemplate,
    DocumentType,
    GeneratedDocument,
)
from app.services import DocumentService

logger = get_logger(__name__)
router = APIRouter()

# Global service instance (will be set from main.py)
_document_service: Optional[DocumentService] = None


def set_document_service(service: DocumentService):
    """Set the document service instance"""
    global _document_service
    _document_service = service


def get_document_service() -> DocumentService:
    """Get the document service instance"""
    if _document_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document service not initialized"
        )
    return _document_service


# ============================================================================
# Request/Response Models
# ============================================================================


class TemplateSearchRequest(BaseModel):
    """Template search request"""

    query: Optional[str] = Field(None, description="Search query")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    language: str = Field("ka", description="Language: 'ka' or 'en'")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")


class TemplateSearchResponse(BaseModel):
    """Template search response"""

    templates: List[DocumentTemplate]
    total: int


class DocumentTypesResponse(BaseModel):
    """Document types response"""

    types: List[DocumentType]
    total: int


class DocumentGenerationResponse(BaseModel):
    """Document generation response"""

    document: GeneratedDocument
    processing_time_ms: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/documents/types", response_model=DocumentTypesResponse)
async def list_document_types(
    language: str = "ka"
):
    """
    List all available document types

    Args:
        language: Language filter ('ka' or 'en')

    Returns:
        List of document types with descriptions
    """
    start_time = time.time()

    try:
        service = get_document_service()
        types = await service.list_document_types(language=language)

        logger.info(
            f"Listed {len(types)} document types",
            extra={"language": language}
        )

        return DocumentTypesResponse(
            types=types,
            total=len(types)
        )

    except Exception as e:
        logger.error(f"Error listing document types: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list document types: {str(e)}"
        )


@router.get("/documents/templates", response_model=TemplateSearchResponse)
async def search_templates(
    query: Optional[str] = None,
    document_type: Optional[str] = None,
    language: str = "ka",
    limit: int = 10
):
    """
    Search for document templates

    Args:
        query: Search query (searches in name and category)
        document_type: Filter by document type
        language: Language filter ('ka' or 'en')
        limit: Maximum number of results

    Returns:
        List of matching templates
    """
    start_time = time.time()

    try:
        service = get_document_service()

        if query:
            templates = await service.search_templates(
                query=query,
                language=language,
                limit=limit
            )
        else:
            # If no query, get all templates of the specified type
            templates = await service.search_templates(
                query="",
                language=language,
                limit=limit
            )

            # Filter by document type if specified
            if document_type:
                templates = [t for t in templates if t.type == document_type]

        logger.info(
            f"Found {len(templates)} templates",
            extra={
                "query": query,
                "document_type": document_type,
                "language": language
            }
        )

        return TemplateSearchResponse(
            templates=templates,
            total=len(templates)
        )

    except Exception as e:
        logger.error(f"Error searching templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search templates: {str(e)}"
        )


@router.get("/documents/templates/{template_id}", response_model=DocumentTemplate)
async def get_template(template_id: str):
    """
    Get a specific template by ID

    Args:
        template_id: Template identifier

    Returns:
        Template details including variables and content
    """
    try:
        service = get_document_service()
        template_store = service.template_store

        if not template_store or template_id not in template_store.templates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        template = template_store.templates[template_id]

        logger.info(f"Retrieved template: {template_id}")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.post("/documents/generate", response_model=DocumentGenerationResponse)
async def generate_document(request: DocumentGenerationRequest):
    """
    Generate a document from a template

    Args:
        request: Document generation request with template ID and variables

    Returns:
        Generated document with content and metadata
    """
    start_time = time.time()

    try:
        service = get_document_service()

        logger.info(
            f"Generating document from template: {request.template_id}",
            extra={
                "template_id": request.template_id,
                "output_format": request.output_format,
                "use_llm": request.use_llm
            }
        )

        # Generate document
        document = await service.generate_document(request)

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Document generated successfully",
            extra={
                "template_id": request.template_id,
                "output_format": document.output_format,
                "processing_time_ms": processing_time_ms,
                "warnings": len(document.warnings)
            }
        )

        return DocumentGenerationResponse(
            document=document,
            processing_time_ms=processing_time_ms
        )

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )
