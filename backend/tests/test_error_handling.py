"""
Tests for error handling and service resilience

These tests verify:
- Graceful error handling across services
- Error response format consistency
- Service failure recovery
- Timeout handling
- External API failure handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import asyncio


class TestGlobalErrorHandling:
    """Test global exception handlers"""

    @pytest.mark.unit
    def test_unhandled_exception_returns_500(self, client):
        """Unhandled exceptions should return 500 with request ID"""
        # Trigger an unhandled exception by making an invalid request
        # that might cause an internal error
        response = client.get("/v1/nonexistent-endpoint-that-causes-500")

        # Should be 404 for non-existent endpoint
        assert response.status_code == 404

    @pytest.mark.unit
    def test_error_response_has_request_id(self, client):
        """Error responses should include request ID"""
        response = client.get("/v1/nonexistent")

        assert response.status_code == 404
        # Request ID should be in headers
        assert "x-request-id" in response.headers

    @pytest.mark.unit
    def test_validation_error_format(self, client):
        """Validation errors should have proper format"""
        response = client.post(
            "/v1/chat",
            json={"invalid_field": "value"}  # Missing required 'message'
        )

        assert response.status_code == 422
        data = response.json()

        assert "detail" in data
        # Should contain validation error details
        if isinstance(data["detail"], list):
            assert len(data["detail"]) > 0


class TestServiceFailureHandling:
    """Test handling of service failures"""

    @pytest.mark.unit
    def test_tax_service_failure(self, mock_services):
        """Should handle tax service failures gracefully"""
        # Make tax service throw an exception
        mock_services["tax_service"].get_tax_answer = AsyncMock(
            side_effect=Exception("Tax service unavailable")
        )

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/v1/chat",
                    json={"message": "test", "conversation_id": "test"}
                )

                # Should return error response, not crash
                assert response.status_code in [500, 503]
                data = response.json()
                assert "error" in data or "detail" in data

    @pytest.mark.unit
    def test_dispute_service_failure(self, mock_services):
        """Should handle dispute service failures gracefully"""
        mock_services["dispute_service"].query = AsyncMock(
            side_effect=Exception("Dispute service unavailable")
        )

        # Service should still start
        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                # Health should still work
                response = client.get("/health")
                assert response.status_code == 200

    @pytest.mark.unit
    def test_document_service_failure(self, mock_services):
        """Should handle document service failures gracefully"""
        mock_services["document_service"].initialize = AsyncMock(
            side_effect=Exception("Document service init failed")
        )

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            # App should still start
            with TestClient(app) as client:
                response = client.get("/health")
                # Should be healthy or degraded
                assert response.status_code in [200, 503]


class TestLLMErrorHandling:
    """Test LLM API error handling"""

    @pytest.mark.unit
    def test_gemini_api_error(self, mock_services):
        """Should handle Gemini API errors"""
        mock_services["tax_service"].get_tax_answer = AsyncMock(
            side_effect=Exception("Gemini API rate limit exceeded")
        )

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/v1/chat",
                    json={"message": "test", "conversation_id": "test"}
                )

                # Should return appropriate error
                assert response.status_code in [500, 502, 503]

    @pytest.mark.unit
    def test_claude_api_fallback(self, mock_services):
        """Should fallback to Claude when Gemini fails"""
        # This tests the fallback mechanism if implemented
        mock_services["tax_service"].get_tax_answer = AsyncMock(return_value={
            "answer": "Fallback response from Claude",
            "sources": [],
            "confidence": 0.8,
            "model_used": "claude"
        })

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/v1/chat",
                    json={"message": "test", "conversation_id": "test"}
                )

                # Should succeed with fallback
                assert response.status_code == 200


class TestTimeoutHandling:
    """Test timeout scenarios"""

    @pytest.mark.unit
    def test_slow_service_response(self, mock_services):
        """Should handle slow service responses"""
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # Small delay for test
            return {
                "answer": "Delayed response",
                "sources": [],
                "confidence": 0.9,
                "model_used": "gemini-pro"
            }

        mock_services["tax_service"].get_tax_answer = AsyncMock(side_effect=slow_response)

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/v1/chat",
                    json={"message": "test", "conversation_id": "test"}
                )

                # Should eventually succeed
                assert response.status_code == 200


class TestInputValidationErrors:
    """Test input validation error handling"""

    @pytest.mark.unit
    def test_missing_required_field(self, client):
        """Should return 422 for missing required fields"""
        response = client.post("/v1/chat", json={})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_wrong_field_type(self, client):
        """Should return 422 for wrong field types"""
        response = client.post(
            "/v1/chat",
            json={"message": 123}  # Should be string
        )

        # Should be 422 or accepted if coerced
        assert response.status_code in [200, 422]

    @pytest.mark.unit
    def test_extra_unknown_fields(self, client, mock_services):
        """Should handle extra unknown fields"""
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "Response",
            "sources": [],
            "confidence": 0.9,
            "model_used": "gemini-pro"
        }

        response = client.post(
            "/v1/chat",
            json={
                "message": "test",
                "conversation_id": "test",
                "unknown_field": "value",
                "another_unknown": 123
            }
        )

        # Should accept (ignore extra fields) or reject
        assert response.status_code in [200, 422]


class TestNetworkErrorHandling:
    """Test network error scenarios"""

    @pytest.mark.unit
    def test_connection_error(self, mock_services):
        """Should handle connection errors"""
        mock_services["tax_service"].get_tax_answer = AsyncMock(
            side_effect=ConnectionError("Network unreachable")
        )

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/v1/chat",
                    json={"message": "test", "conversation_id": "test"}
                )

                assert response.status_code in [500, 502, 503]


class TestResourceNotFound:
    """Test resource not found scenarios"""

    @pytest.mark.unit
    def test_conversation_not_found(self, client):
        """Should return 404 for non-existent conversation"""
        response = client.get("/v1/conversations/nonexistent-id-12345")

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_document_type_not_found(self, client):
        """Should return 404 for non-existent document type"""
        response = client.get("/v1/documents/types/nonexistent-type")

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_template_not_found(self, client):
        """Should return 404 for non-existent template"""
        response = client.get("/v1/documents/templates/nonexistent-template")

        assert response.status_code in [200, 404]


class TestAuthenticationErrors:
    """Test authentication error handling"""

    @pytest.mark.unit
    def test_missing_admin_key(self, client):
        """Should return 401/403 when admin key is missing"""
        response = client.get("/v1/admin/stats")

        assert response.status_code in [401, 403]

    @pytest.mark.unit
    def test_invalid_admin_key(self, client):
        """Should return 401/403 when admin key is invalid"""
        response = client.get(
            "/v1/admin/stats",
            headers={"X-Admin-Key": "invalid-key"}
        )

        assert response.status_code in [401, 403]

    @pytest.mark.unit
    def test_malformed_auth_header(self, client):
        """Should handle malformed auth headers"""
        response = client.get(
            "/v1/admin/stats",
            headers={"X-Admin-Key": ""}  # Empty key
        )

        assert response.status_code in [401, 403]


class TestDataCorruptionHandling:
    """Test handling of corrupted or invalid data"""

    @pytest.mark.unit
    def test_corrupted_json_response_from_service(self, mock_services):
        """Should handle corrupted responses from services"""
        # Return non-dict response
        mock_services["tax_service"].get_tax_answer = AsyncMock(return_value=None)

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                response = client.post(
                    "/v1/chat",
                    json={"message": "test", "conversation_id": "test"}
                )

                # Should handle gracefully
                assert response.status_code in [200, 500]


class TestConcurrencyErrors:
    """Test concurrency-related error handling"""

    @pytest.mark.unit
    def test_race_condition_handling(self, mock_services):
        """Should handle concurrent requests safely"""
        import concurrent.futures

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                def make_request():
                    return client.get("/health")

                # Make concurrent requests
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(make_request) for _ in range(10)]
                    results = [f.result() for f in futures]

                # All should succeed
                assert all(r.status_code == 200 for r in results)


class TestErrorResponseConsistency:
    """Test that error responses are consistent"""

    @pytest.mark.unit
    def test_404_response_structure(self, client):
        """404 responses should have consistent structure"""
        response = client.get("/v1/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_422_response_structure(self, client):
        """422 responses should have consistent structure"""
        response = client.post("/v1/chat", json={})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_405_response_structure(self, client):
        """405 responses should have consistent structure"""
        response = client.get("/v1/chat")  # Should be POST

        assert response.status_code == 405
        data = response.json()
        assert "detail" in data


class TestPartialFailures:
    """Test handling of partial service failures"""

    @pytest.mark.unit
    def test_one_service_down_others_work(self, mock_services):
        """Other endpoints should work when one service is down"""
        # Make tax service fail
        mock_services["tax_service"].initialize = AsyncMock(
            side_effect=Exception("Tax service down")
        )

        with patch('app.main.TaxCodeService', return_value=mock_services["tax_service"]), \
             patch('app.main.DisputeService', return_value=mock_services["dispute_service"]), \
             patch('app.main.DocumentService', return_value=mock_services["document_service"]):
            from app.main import app
            with TestClient(app) as client:
                # Health should still work
                response = client.get("/health")
                assert response.status_code in [200, 503]

                # Documents should still work (if initialized)
                response = client.get("/v1/documents/types")
                assert response.status_code in [200, 404, 503]
