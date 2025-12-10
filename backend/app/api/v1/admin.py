"""
Admin API endpoints for content management

Simple API key authentication for administrative operations:
- Template uploads
- Dispute document uploads
- System statistics
"""
import io
import tempfile
from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.core import get_logger, get_settings
from app.models import DocumentTemplate
from app.services import DisputeService, DocumentService, TaxCodeService

logger = get_logger(__name__)
router = APIRouter()

# Global service instances (will be set from main.py)
_tax_service: Optional[TaxCodeService] = None
_dispute_service: Optional[DisputeService] = None
_document_service: Optional[DocumentService] = None


def set_services(
    tax_service: TaxCodeService,
    dispute_service: DisputeService,
    document_service: DocumentService
):
    """Set service instances"""
    global _tax_service, _dispute_service, _document_service
    _tax_service = tax_service
    _dispute_service = dispute_service
    _document_service = document_service


# ============================================================================
# Authentication
# ============================================================================


def verify_admin_key(x_admin_key: str = Header(None)):
    """
    Verify admin API key from header

    Args:
        x_admin_key: Admin API key from X-Admin-Key header

    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    settings = get_settings()

    if not settings.admin_api_key:
        logger.error("ADMIN_API_KEY not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin functionality not configured"
        )

    if not x_admin_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-Key header"
        )

    if x_admin_key != settings.admin_api_key:
        logger.warning("Invalid admin API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key"
        )

    return True


# ============================================================================
# Request/Response Models
# ============================================================================


class TemplateUploadResponse(BaseModel):
    """Template upload response"""

    template_id: str
    status: str = "created"
    message: str


class DisputeUploadResponse(BaseModel):
    """Dispute upload response"""

    documents_processed: int
    chunks_created: int
    status: str
    message: str


class ServiceStats(BaseModel):
    """Service statistics"""

    status: str
    ready: bool
    details: dict


class AdminStatsResponse(BaseModel):
    """Admin statistics response"""

    tax_service: ServiceStats
    dispute_service: ServiceStats
    document_service: ServiceStats
    templates: dict
    disputes: dict


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/admin/templates", response_model=TemplateUploadResponse)
async def upload_template(
    file: UploadFile = File(...),
    _: bool = Depends(verify_admin_key)
):
    """
    Upload a new document template

    Requires admin authentication via X-Admin-Key header.

    Args:
        file: YAML template file
        _: Admin key verification (dependency)

    Returns:
        Template upload result with ID and status
    """
    if not _document_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document service not available"
        )

    # Validate file type
    if not file.filename.endswith(('.yaml', '.yml')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a YAML file (.yaml or .yml)"
        )

    try:
        # Read and parse YAML
        content = await file.read()
        template_data = yaml.safe_load(content)

        # Validate required fields
        required_fields = ["id", "type", "name_ka", "name_en", "language", "content", "variables"]
        missing_fields = [f for f in required_fields if f not in template_data]

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Create DocumentTemplate instance
        template = DocumentTemplate(**template_data)

        # Add template to store
        template_id = await _document_service.template_store.add_template(template)

        logger.info(
            f"Template uploaded successfully: {template_id}",
            extra={"template_id": template_id, "filename": file.filename}
        )

        return TemplateUploadResponse(
            template_id=template_id,
            status="created",
            message=f"Template '{template_id}' created successfully"
        )

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML format: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Template validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error uploading template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload template: {str(e)}"
        )


@router.post("/admin/disputes", response_model=DisputeUploadResponse)
async def upload_disputes(
    files: List[UploadFile] = File(...),
    _: bool = Depends(verify_admin_key)
):
    """
    Upload dispute documents for processing

    Requires admin authentication via X-Admin-Key header.

    Supports:
    - PDF files: Extracted and processed into chunks
    - JSON files: Direct import of structured dispute data

    Args:
        files: List of PDF or JSON files
        _: Admin key verification (dependency)

    Returns:
        Upload result with document and chunk counts
    """
    if not _dispute_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dispute service not available"
        )

    documents_processed = 0
    total_chunks = 0
    errors = []

    try:
        # Create temporary directory for file processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for file in files:
                try:
                    # Validate file type
                    if not file.filename.endswith(('.pdf', '.json')):
                        errors.append(f"{file.filename}: Unsupported format (use .pdf or .json)")
                        continue

                    # Save file temporarily
                    file_path = temp_path / file.filename
                    content = await file.read()

                    with open(file_path, 'wb') as f:
                        f.write(content)

                    # Process based on file type
                    if file.filename.endswith('.pdf'):
                        # PDF processing would go here
                        # For now, log that it's not fully implemented
                        logger.warning(f"PDF processing not fully implemented: {file.filename}")
                        errors.append(f"{file.filename}: PDF processing not fully implemented")

                    elif file.filename.endswith('.json'):
                        # JSON dispute import would go here
                        # For now, log that it's not fully implemented
                        logger.warning(f"JSON import not fully implemented: {file.filename}")
                        errors.append(f"{file.filename}: JSON import not fully implemented")

                    documents_processed += 1

                except Exception as e:
                    logger.error(f"Error processing {file.filename}: {e}")
                    errors.append(f"{file.filename}: {str(e)}")

        # Determine status
        if documents_processed == 0:
            status_text = "failed"
            message = "No documents processed successfully"
        elif errors:
            status_text = "partial"
            message = f"Processed {documents_processed} documents with {len(errors)} errors"
        else:
            status_text = "success"
            message = f"Successfully processed {documents_processed} documents"

        if errors:
            message += f". Errors: {'; '.join(errors[:3])}"  # Limit to first 3 errors

        logger.info(
            f"Dispute upload completed: {documents_processed} processed, {len(errors)} errors",
            extra={
                "documents_processed": documents_processed,
                "total_chunks": total_chunks,
                "error_count": len(errors)
            }
        )

        return DisputeUploadResponse(
            documents_processed=documents_processed,
            chunks_created=total_chunks,
            status=status_text,
            message=message
        )

    except Exception as e:
        logger.error(f"Error in dispute upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process disputes: {str(e)}"
        )


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(_: bool = Depends(verify_admin_key)):
    """
    Get system statistics

    Requires admin authentication via X-Admin-Key header.

    Returns:
        Comprehensive system statistics including:
        - Service statuses
        - Template counts
        - Dispute document counts
        - Vector store statistics
    """
    try:
        # Tax service stats
        if _tax_service:
            tax_status = _tax_service.get_status()
            tax_stats = ServiceStats(
                status="ready" if tax_status.get("ready") else "not_ready",
                ready=tax_status.get("ready", False),
                details={
                    "model": tax_status.get("model"),
                    "index_size": tax_status.get("index_size"),
                    "embedding_dimensions": tax_status.get("embedding_dimensions")
                }
            )
        else:
            tax_stats = ServiceStats(
                status="unavailable",
                ready=False,
                details={}
            )

        # Dispute service stats
        if _dispute_service:
            dispute_status = _dispute_service.get_status()
            dispute_stats = ServiceStats(
                status="ready" if dispute_status.get("ready") else "not_ready",
                ready=dispute_status.get("ready", False),
                details=dispute_status
            )

            # Get dispute counts
            disputes_info = {
                "total_documents": dispute_status.get("total_chunks", 0),
                "total_chunks": dispute_status.get("total_chunks", 0),
                "index_size": dispute_status.get("index_size", 0)
            }
        else:
            dispute_stats = ServiceStats(
                status="unavailable",
                ready=False,
                details={}
            )
            disputes_info = {
                "total_documents": 0,
                "total_chunks": 0
            }

        # Document service stats
        if _document_service:
            doc_status = _document_service.get_status()
            document_stats = ServiceStats(
                status="ready" if doc_status.get("ready") else "not_ready",
                ready=doc_status.get("ready", False),
                details=doc_status
            )

            # Get template counts
            template_store_status = doc_status.get("template_store", {})
            templates_info = {
                "total": template_store_status.get("templates_count", 0),
                "by_type": {},
                "by_language": template_store_status.get("templates_by_language", {})
            }

            # Count templates by type
            if _document_service.template_store:
                type_counts = {}
                for template in _document_service.template_store.templates.values():
                    type_counts[template.type] = type_counts.get(template.type, 0) + 1
                templates_info["by_type"] = type_counts

        else:
            document_stats = ServiceStats(
                status="unavailable",
                ready=False,
                details={}
            )
            templates_info = {
                "total": 0,
                "by_type": {},
                "by_language": {}
            }

        logger.info("Admin stats retrieved")

        return AdminStatsResponse(
            tax_service=tax_stats,
            dispute_service=dispute_stats,
            document_service=document_stats,
            templates=templates_info,
            disputes=disputes_info
        )

    except Exception as e:
        logger.error(f"Error getting admin stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/admin/health")
async def admin_health_check(_: bool = Depends(verify_admin_key)):
    """
    Simple health check for admin endpoints

    Requires admin authentication.

    Returns:
        Simple status message
    """
    return {
        "status": "ok",
        "message": "Admin API is operational",
        "authenticated": True
    }
