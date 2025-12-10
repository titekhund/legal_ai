"""
Health check and status endpoints
"""
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends

from app.core import get_logger
from app.services import TaxCodeService

logger = get_logger(__name__)
router = APIRouter()

# Global service instances (will be initialized in main.py)
_tax_service: TaxCodeService = None


def set_tax_service(service: TaxCodeService):
    """Set the tax service instance"""
    global _tax_service
    _tax_service = service


def get_tax_service() -> TaxCodeService:
    """Get the tax service instance"""
    return _tax_service


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint

    Returns:
        Simple health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/status")
async def service_status():
    """
    Detailed service status endpoint

    Returns:
        Status of all services (tax, dispute, document)
    """
    # Get tax service status
    tax_service = get_tax_service()

    if tax_service:
        tax_status = tax_service.get_status()
        tax_ready = tax_status.get("file_upload_status") == "ready"

        tax_service_status = {
            "ready": tax_ready,
            "model": tax_status.get("model_name"),
            "file_uploaded": tax_ready,
            "file_path": tax_status.get("tax_code_path"),
        }
    else:
        tax_service_status = {
            "ready": False,
            "message": "Tax service not initialized"
        }

    return {
        "tax_service": tax_service_status,
        "dispute_service": {
            "ready": False,
            "message": "Coming in Phase 2"
        },
        "document_service": {
            "ready": False,
            "message": "Coming in Phase 3"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
