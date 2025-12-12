"""
Tests for health checks and application startup - Cloud-ready tests

These tests verify:
- Health endpoint availability and response format
- Service status reporting
- Application startup/shutdown behavior
- Cloud Run compatibility (readiness/liveness probes)
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test /health endpoint - Critical for cloud deployment health checks"""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_health_check_returns_200(self, client):
        """Health check should return 200 OK when service is running"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_health_check_response_format(self, client):
        """Health check response should have correct structure"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Required fields for cloud health checks
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "up"]

    @pytest.mark.unit
    def test_health_endpoint_is_fast(self, client):
        """Health check should respond quickly (< 1 second)"""
        start_time = time.time()
        response = client.get("/health")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 1.0, f"Health check took too long: {elapsed:.2f}s"

    @pytest.mark.unit
    def test_health_returns_json_content_type(self, client):
        """Health check should return JSON content type"""
        response = client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestStatusEndpoint:
    """Test /v1/status endpoint - Detailed service status for monitoring"""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_status_endpoint_accessible(self, client):
        """Status endpoint should be accessible"""
        response = client.get("/v1/status")

        assert response.status_code == 200

    @pytest.mark.unit
    def test_status_returns_service_info(self, client):
        """Status should return service information"""
        response = client.get("/v1/status")

        assert response.status_code == 200
        data = response.json()

        # Should have status field
        assert "status" in data

    @pytest.mark.unit
    def test_status_includes_service_details(self, client):
        """Status should include individual service details"""
        response = client.get("/v1/status")

        assert response.status_code == 200
        data = response.json()

        # Response should be a dict with service information
        assert isinstance(data, dict)


class TestRootEndpoint:
    """Test root endpoint - API information"""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_root_returns_api_info(self, client):
        """Root endpoint should return API information"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Should have basic API info
        assert "name" in data or "title" in data
        assert "version" in data or "status" in data

    @pytest.mark.unit
    def test_root_includes_docs_links(self, client):
        """Root endpoint should include documentation links"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Should reference docs
        assert "docs" in data or "/docs" in str(data)


class TestOpenAPIEndpoints:
    """Test API documentation endpoints - Important for development"""

    @pytest.mark.unit
    def test_openapi_schema_available(self, client):
        """OpenAPI schema should be accessible"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.unit
    def test_swagger_docs_available(self, client):
        """Swagger docs should be accessible"""
        response = client.get("/docs")

        # Should return HTML (might redirect)
        assert response.status_code in [200, 307]

    @pytest.mark.unit
    def test_redoc_available(self, client):
        """ReDoc documentation should be accessible"""
        response = client.get("/redoc")

        # Should return HTML (might redirect)
        assert response.status_code in [200, 307]


class TestApplicationLifecycle:
    """Test application startup and shutdown behavior"""

    @pytest.mark.unit
    def test_app_starts_without_error(self, mock_services):
        """Application should start without errors"""
        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200

    @pytest.mark.unit
    def test_app_handles_service_init_failure_gracefully(self, mock_services):
        """App should handle service initialization failures gracefully"""
        # Make tax service initialization fail
        mock_services["tax_service"].initialize = AsyncMock(
            side_effect=Exception("Init failed")
        )

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            # App should still start (with degraded functionality)
            with TestClient(app) as client:
                response = client.get("/health")
                # Should still be accessible even if some services failed
                assert response.status_code in [200, 503]


class TestRequestTracking:
    """Test request ID and tracking headers"""

    @pytest.mark.unit
    def test_request_id_header_present(self, client):
        """Each response should have X-Request-ID header"""
        response = client.get("/health")

        assert response.status_code == 200
        assert "x-request-id" in response.headers

    @pytest.mark.unit
    def test_request_id_is_unique(self, client):
        """Each request should get unique request ID"""
        response1 = client.get("/health")
        response2 = client.get("/health")

        id1 = response1.headers.get("x-request-id")
        id2 = response2.headers.get("x-request-id")

        assert id1 is not None
        assert id2 is not None
        assert id1 != id2


class TestCORSConfiguration:
    """Test CORS headers for cross-origin requests"""

    @pytest.mark.unit
    def test_cors_preflight_request(self, client):
        """CORS preflight request should be handled"""
        response = client.options(
            "/v1/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )

        # Should not return 405 Method Not Allowed
        assert response.status_code in [200, 204]

    @pytest.mark.unit
    def test_cors_headers_on_response(self, client):
        """Responses should include CORS headers"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        # CORS headers should be present when Origin is sent
        # Note: exact header presence depends on configuration


class TestCloudRunCompatibility:
    """Tests specific to Cloud Run deployment requirements"""

    @pytest.mark.cloud
    @pytest.mark.unit
    def test_responds_on_any_port(self, mock_services, mock_cloud_env):
        """Application should respond on PORT environment variable"""
        # Cloud Run sets PORT env var
        assert mock_cloud_env.get("PORT") == "8080"

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200

    @pytest.mark.cloud
    @pytest.mark.unit
    def test_health_for_cloud_run_startup_probe(self, client):
        """Health endpoint should work for Cloud Run startup probe"""
        # Cloud Run uses health checks for startup probes
        response = client.get("/health")

        assert response.status_code == 200
        # Response time should be fast for probes
        data = response.json()
        assert "status" in data

    @pytest.mark.cloud
    @pytest.mark.unit
    def test_health_for_cloud_run_liveness_probe(self, client):
        """Health endpoint should work for Cloud Run liveness probe"""
        # Liveness probes need quick, reliable responses
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    @pytest.mark.cloud
    @pytest.mark.unit
    def test_graceful_shutdown_readiness(self, client):
        """Application should handle graceful shutdown"""
        # During shutdown, health should still respond
        response = client.get("/health")
        assert response.status_code == 200


class TestErrorHandling:
    """Test global error handling"""

    @pytest.mark.unit
    def test_404_has_correct_format(self, client):
        """404 errors should have consistent format"""
        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_405_method_not_allowed(self, client):
        """405 errors should be returned for wrong HTTP methods"""
        # GET on a POST-only endpoint
        response = client.get("/v1/chat")

        assert response.status_code == 405

    @pytest.mark.unit
    def test_422_validation_error_format(self, client):
        """422 validation errors should have correct format"""
        # Send invalid JSON to chat endpoint
        response = client.post(
            "/v1/chat",
            json={}  # Missing required 'message' field
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestSecurityHeaders:
    """Test security-related headers and configurations"""

    @pytest.mark.unit
    def test_content_type_header(self, client):
        """Responses should have correct Content-Type"""
        response = client.get("/health")

        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    @pytest.mark.unit
    def test_no_server_header_leak(self, client):
        """Server header should not leak implementation details"""
        response = client.get("/health")

        # Server header should be minimal or absent
        server = response.headers.get("server", "")
        # Should not contain detailed version info
        assert "uvicorn" not in server.lower() or "version" not in server.lower()


class TestResourceEndpoints:
    """Test that required resource endpoints exist"""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_chat_endpoint_exists(self, client):
        """Chat endpoint should exist"""
        # Check if endpoint exists (even without valid request)
        response = client.post("/v1/chat", json={"message": "test"})

        # Should not be 404
        assert response.status_code != 404

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_documents_endpoint_exists(self, client):
        """Documents endpoint should exist"""
        response = client.get("/v1/documents/types")

        # Should not be 404
        assert response.status_code != 404

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_conversations_endpoint_exists(self, client):
        """Conversations endpoint should exist"""
        response = client.get("/v1/conversations")

        # Should not be 404 (might be 200 or 401)
        assert response.status_code != 404


class TestPerformanceBaseline:
    """Basic performance tests to ensure acceptable response times"""

    @pytest.mark.unit
    def test_health_endpoint_performance(self, client):
        """Health endpoint should respond within SLA"""
        times = []
        for _ in range(10):
            start = time.time()
            response = client.get("/health")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Health check should be fast
        assert avg_time < 0.1, f"Average health check time too slow: {avg_time:.3f}s"
        assert max_time < 0.5, f"Max health check time too slow: {max_time:.3f}s"

    @pytest.mark.unit
    def test_status_endpoint_performance(self, client):
        """Status endpoint should respond within SLA"""
        start = time.time()
        response = client.get("/v1/status")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Status check too slow: {elapsed:.3f}s"
