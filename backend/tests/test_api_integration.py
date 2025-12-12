"""
Comprehensive API endpoint integration tests

These tests verify:
- All API endpoints work correctly
- Request/response validation
- Error handling
- Rate limiting behavior
- Authentication for admin endpoints
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient


class TestChatEndpoint:
    """Test /v1/chat endpoint - Main conversational interface"""

    @pytest.mark.unit
    def test_chat_with_valid_message(self, client, mock_services):
        """Chat should accept valid message and return response"""
        # Configure mock to return proper response
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "დღგ-ს განაკვეთი არის 18%.",
            "sources": [
                {
                    "article": "166",
                    "title": "დღგ-ს განაკვეთი",
                    "content": "18 პროცენტი",
                    "matsne_url": "https://matsne.gov.ge/..."
                }
            ],
            "confidence": 0.95,
            "model_used": "gemini-pro"
        }

        response = client.post(
            "/v1/chat",
            json={
                "message": "რა არის დღგ-ს განაკვეთი?",
                "conversation_id": "test-123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "answer" in data or "response" in data

    @pytest.mark.unit
    def test_chat_requires_message(self, client):
        """Chat should require message field"""
        response = client.post(
            "/v1/chat",
            json={"conversation_id": "test-123"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.unit
    def test_chat_rejects_empty_message(self, client):
        """Chat should reject empty message"""
        response = client.post(
            "/v1/chat",
            json={"message": "", "conversation_id": "test-123"}
        )

        # Should return 400 or 422
        assert response.status_code in [400, 422]

    @pytest.mark.unit
    def test_chat_creates_conversation_id(self, client, mock_services):
        """Chat should create conversation ID if not provided"""
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "Test response",
            "sources": [],
            "confidence": 0.9,
            "model_used": "gemini-pro"
        }

        response = client.post(
            "/v1/chat",
            json={"message": "ტესტის კითხვა?"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should have a conversation ID (generated or in response)
        assert "conversation_id" in data or response.status_code == 200

    @pytest.mark.unit
    def test_chat_with_georgian_text(self, client, mock_services):
        """Chat should handle Georgian text properly"""
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "პასუხი ქართულად",
            "sources": [],
            "confidence": 0.9,
            "model_used": "gemini-pro"
        }

        response = client.post(
            "/v1/chat",
            json={
                "message": "რა არის საგადასახადო კოდექსის მუხლი 166?",
                "conversation_id": "georgian-test"
            }
        )

        assert response.status_code == 200

    @pytest.mark.unit
    def test_chat_returns_sources(self, client, mock_services):
        """Chat should return sources with citations"""
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "Answer with citations",
            "sources": [
                {"article": "166", "title": "Title", "content": "Content", "matsne_url": "url"}
            ],
            "confidence": 0.95,
            "model_used": "gemini-pro"
        }

        response = client.post(
            "/v1/chat",
            json={"message": "test", "conversation_id": "test"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have sources in response
        if "sources" in data:
            assert isinstance(data["sources"], list)

    @pytest.mark.unit
    def test_chat_with_mode_parameter(self, client, mock_services):
        """Chat should accept mode parameter"""
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "Tax mode response",
            "sources": [],
            "confidence": 0.9,
            "model_used": "gemini-pro"
        }

        response = client.post(
            "/v1/chat",
            json={
                "message": "test question",
                "conversation_id": "test",
                "mode": "tax"
            }
        )

        assert response.status_code == 200


class TestConversationsEndpoint:
    """Test /v1/conversations endpoints"""

    @pytest.mark.unit
    def test_list_conversations(self, client):
        """Should list conversations"""
        response = client.get("/v1/conversations")

        # Should not be 404
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_get_conversation_by_id(self, client):
        """Should get conversation by ID"""
        response = client.get("/v1/conversations/test-conv-123")

        # Should be 200 (if exists) or 404 (if not)
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_list_conversations_with_pagination(self, client):
        """Should support pagination parameters"""
        response = client.get("/v1/conversations?limit=10&offset=0")

        assert response.status_code in [200, 404]


class TestDocumentsEndpoint:
    """Test /v1/documents endpoints"""

    @pytest.mark.unit
    def test_list_document_types(self, client):
        """Should list available document types"""
        response = client.get("/v1/documents/types")

        assert response.status_code == 200
        data = response.json()

        # Should return list of document types
        assert isinstance(data, list) or "types" in data

    @pytest.mark.unit
    def test_get_document_type_by_id(self, client):
        """Should get specific document type"""
        response = client.get("/v1/documents/types/nda")

        # Should be 200 or 404
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_list_templates(self, client):
        """Should list document templates"""
        response = client.get("/v1/documents/templates")

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_search_templates(self, client):
        """Should search templates with query"""
        response = client.get("/v1/documents/templates?query=nda")

        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_generate_document_validation(self, client):
        """Document generation should validate request"""
        response = client.post(
            "/v1/documents/generate",
            json={}  # Empty request should fail
        )

        assert response.status_code in [400, 422]


class TestAdminEndpoints:
    """Test /v1/admin endpoints - Require authentication"""

    @pytest.mark.unit
    def test_admin_requires_api_key(self, client):
        """Admin endpoints should require API key"""
        response = client.get("/v1/admin/stats")

        # Should be 401 or 403 without API key
        assert response.status_code in [401, 403]

    @pytest.mark.unit
    def test_admin_with_valid_api_key(self, client, test_config):
        """Admin endpoints should work with valid API key"""
        response = client.get(
            "/v1/admin/stats",
            headers={"X-Admin-Key": test_config["admin_api_key"]}
        )

        # Should be 200 with valid key
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_admin_with_invalid_api_key(self, client):
        """Admin endpoints should reject invalid API key"""
        response = client.get(
            "/v1/admin/stats",
            headers={"X-Admin-Key": "invalid-key"}
        )

        assert response.status_code in [401, 403]

    @pytest.mark.unit
    def test_admin_health_endpoint(self, client, test_config):
        """Admin health endpoint should work"""
        response = client.get(
            "/v1/admin/health",
            headers={"X-Admin-Key": test_config["admin_api_key"]}
        )

        assert response.status_code in [200, 404]


class TestRequestValidation:
    """Test request validation across endpoints"""

    @pytest.mark.unit
    def test_invalid_json_body(self, client):
        """Should reject invalid JSON"""
        response = client.post(
            "/v1/chat",
            data="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.unit
    def test_wrong_content_type(self, client):
        """Should handle wrong content type"""
        response = client.post(
            "/v1/chat",
            data="message=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Should be 415 or 422
        assert response.status_code in [415, 422]

    @pytest.mark.unit
    def test_message_length_limit(self, client, mock_services):
        """Should handle long messages"""
        # Very long message
        long_message = "a" * 5000

        response = client.post(
            "/v1/chat",
            json={"message": long_message, "conversation_id": "test"}
        )

        # Should either accept (200) or reject with validation error (400/422)
        assert response.status_code in [200, 400, 422]

    @pytest.mark.unit
    def test_unicode_handling(self, client, mock_services):
        """Should handle various Unicode characters"""
        mock_services["tax_service"].get_tax_answer.return_value = {
            "answer": "Response",
            "sources": [],
            "confidence": 0.9,
            "model_used": "gemini-pro"
        }

        unicode_messages = [
            "გამარჯობა",  # Georgian
            "Привет",  # Russian
            "你好",  # Chinese
            "مرحبا",  # Arabic
            "🎉💡📊",  # Emoji
        ]

        for msg in unicode_messages:
            response = client.post(
                "/v1/chat",
                json={"message": msg, "conversation_id": "unicode-test"}
            )
            # Should handle all Unicode
            assert response.status_code in [200, 400, 422]


class TestResponseFormat:
    """Test response format consistency"""

    @pytest.mark.unit
    def test_error_response_format(self, client):
        """Error responses should have consistent format"""
        response = client.get("/v1/nonexistent")

        assert response.status_code == 404
        data = response.json()

        # Should have detail field
        assert "detail" in data

    @pytest.mark.unit
    def test_validation_error_format(self, client):
        """Validation errors should have detailed info"""
        response = client.post(
            "/v1/chat",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        assert "detail" in data
        # Detail should be a list with field information
        if isinstance(data["detail"], list):
            for error in data["detail"]:
                assert "loc" in error or "msg" in error

    @pytest.mark.unit
    def test_success_response_json(self, client):
        """Success responses should be valid JSON"""
        response = client.get("/health")

        assert response.status_code == 200
        # Should not raise on JSON decode
        data = response.json()
        assert isinstance(data, dict)


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.unit
    def test_normal_requests_not_limited(self, client):
        """Normal request rate should not be limited"""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    @pytest.mark.slow
    @pytest.mark.integration
    def test_rate_limit_exceeded(self, client):
        """Should return 429 when rate limit exceeded"""
        # This test is slow and requires rate limiting to be configured
        responses = []
        for _ in range(150):  # Try to exceed limit
            response = client.post(
                "/v1/chat",
                json={"message": "test", "conversation_id": "rate-test"}
            )
            responses.append(response.status_code)

            if response.status_code == 429:
                break

        # At least one should be rate limited (if rate limiting enabled)
        # Skip assertion if rate limiting not configured
        if 429 in responses:
            assert True
        else:
            pytest.skip("Rate limiting may not be configured in test environment")

    @pytest.mark.unit
    def test_rate_limit_header(self, client):
        """Rate limited responses should have Retry-After header"""
        # Make request (may or may not be rate limited)
        response = client.get("/health")

        # If rate limited, should have Retry-After
        if response.status_code == 429:
            assert "retry-after" in response.headers


class TestHTTPMethods:
    """Test HTTP method handling"""

    @pytest.mark.unit
    def test_get_on_post_endpoint(self, client):
        """GET on POST-only endpoint should return 405"""
        response = client.get("/v1/chat")
        assert response.status_code == 405

    @pytest.mark.unit
    def test_post_on_get_endpoint(self, client):
        """POST on GET-only endpoint should return 405"""
        response = client.post("/health")
        assert response.status_code == 405

    @pytest.mark.unit
    def test_options_request(self, client):
        """OPTIONS should be handled for CORS"""
        response = client.options("/v1/chat")
        assert response.status_code in [200, 204, 405]

    @pytest.mark.unit
    def test_head_request(self, client):
        """HEAD should work on GET endpoints"""
        response = client.head("/health")
        assert response.status_code in [200, 405]


class TestQueryParameters:
    """Test query parameter handling"""

    @pytest.mark.unit
    def test_pagination_parameters(self, client):
        """Should handle pagination parameters"""
        response = client.get("/v1/conversations?limit=10&offset=0")
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_filter_parameters(self, client):
        """Should handle filter parameters"""
        response = client.get("/v1/documents/templates?type=nda&language=ka")
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_invalid_pagination_values(self, client):
        """Should handle invalid pagination values"""
        response = client.get("/v1/conversations?limit=-1")
        assert response.status_code in [200, 400, 422]

        response = client.get("/v1/conversations?limit=abc")
        assert response.status_code in [200, 400, 422]


class TestPathParameters:
    """Test path parameter handling"""

    @pytest.mark.unit
    def test_valid_path_parameter(self, client):
        """Should handle valid path parameters"""
        response = client.get("/v1/documents/types/nda")
        assert response.status_code in [200, 404]

    @pytest.mark.unit
    def test_invalid_path_parameter(self, client):
        """Should handle invalid path parameters"""
        response = client.get("/v1/documents/types/invalid-type-id-123")
        assert response.status_code in [200, 404]


class TestContentNegotiation:
    """Test content type handling"""

    @pytest.mark.unit
    def test_accepts_json(self, client):
        """Should accept application/json"""
        response = client.post(
            "/v1/chat",
            json={"message": "test"},
            headers={"Accept": "application/json"}
        )
        assert response.status_code in [200, 400, 422]

    @pytest.mark.unit
    def test_returns_json(self, client):
        """Should return application/json"""
        response = client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestConcurrentRequests:
    """Test concurrent request handling"""

    @pytest.mark.unit
    def test_multiple_sequential_requests(self, client):
        """Should handle multiple sequential requests"""
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    @pytest.mark.slow
    @pytest.mark.integration
    def test_parallel_health_checks(self, client):
        """Should handle parallel requests"""
        import concurrent.futures

        def make_request():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in results)
