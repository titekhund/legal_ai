#!/usr/bin/env python3
"""
End-to-end tests for Legal AI API
Tests the full workflow across all three modes: Tax, Dispute, and Document
"""
import asyncio
import httpx
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Base URL for API
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{BASE_URL}/api/v1"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class E2ETestRunner:
    """End-to-end test runner for Legal AI API"""

    def __init__(self, base_url: str = API_V1):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()

    def log_success(self, message: str):
        """Log success message"""
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
        self.passed += 1

    def log_failure(self, message: str, error: Optional[str] = None):
        """Log failure message"""
        print(f"{Colors.RED}✗{Colors.RESET} {message}")
        if error:
            print(f"  {Colors.RED}Error: {error}{Colors.RESET}")
        self.failed += 1

    def log_warning(self, message: str):
        """Log warning message"""
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
        self.warnings += 1

    def log_info(self, message: str):
        """Log info message"""
        print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")

    def log_header(self, message: str):
        """Log section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

    async def test_health_check(self) -> bool:
        """Test API health endpoint"""
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_success("Health check passed")
                    return True
                else:
                    self.log_failure("Health check returned unhealthy status", str(data))
                    return False
            else:
                self.log_failure(f"Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Health check request failed", str(e))
            return False

    async def test_tax_mode(self) -> bool:
        """Test tax consultation mode"""
        self.log_header("Testing Tax Mode")

        # Test 1: Query tax articles
        try:
            response = await self.client.get(
                f"{self.base_url}/tax/articles",
                params={"query": "დღგ", "limit": 5}
            )
            if response.status_code == 200:
                articles = response.json()
                if len(articles) > 0:
                    self.log_success(f"Tax article search returned {len(articles)} results")
                else:
                    self.log_warning("Tax article search returned no results")
            else:
                self.log_failure(f"Tax article search failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Tax article search failed", str(e))
            return False

        # Test 2: Get tax advice
        try:
            response = await self.client.post(
                f"{self.base_url}/tax/advice",
                json={
                    "question": "რა არის დღგ-ის განაკვეთი საქართველოში?",
                    "context": {},
                    "language": "ka"
                }
            )
            if response.status_code == 200:
                advice = response.json()
                if advice.get("answer") and advice.get("cited_articles"):
                    self.log_success("Tax advice generated successfully")
                    self.log_info(f"  Cited {len(advice['cited_articles'])} articles")
                else:
                    self.log_warning("Tax advice missing expected fields")
            else:
                self.log_failure(f"Tax advice failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Tax advice request failed", str(e))
            return False

        return True

    async def test_dispute_mode(self) -> bool:
        """Test dispute analysis mode"""
        self.log_header("Testing Dispute Mode")

        # Test 1: Submit dispute case
        try:
            dispute_data = {
                "case_description": "საგადასახადო ორგანომ დააკისრა დღგ-ის დავალიანება 10000 ლარის ოდენობით, თუმცა კომპანიამ დროულად გადაიხადა ყველა გადასახადი.",
                "taxpayer_info": {
                    "name": "შპს ტესტი",
                    "tax_id": "123456789",
                    "type": " ltd"
                },
                "dispute_type": "tax_assessment",
                "requested_analysis": ["legal_grounds", "recommendations"],
                "language": "ka"
            }
            response = await self.client.post(
                f"{self.base_url}/disputes/analyze",
                json=dispute_data
            )
            if response.status_code == 200:
                analysis = response.json()
                if analysis.get("summary") and analysis.get("legal_grounds"):
                    self.log_success("Dispute analysis completed successfully")
                    self.log_info(f"  Found {len(analysis.get('cited_cases', []))} cited cases")
                    self.log_info(f"  Confidence: {analysis.get('confidence', 'N/A')}")
                else:
                    self.log_warning("Dispute analysis missing expected fields")
            else:
                self.log_failure(f"Dispute analysis failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Dispute analysis request failed", str(e))
            return False

        # Test 2: Search similar cases
        try:
            response = await self.client.get(
                f"{self.base_url}/disputes/cases",
                params={"query": "დღგ", "limit": 3}
            )
            if response.status_code == 200:
                cases = response.json()
                if isinstance(cases, list):
                    self.log_success(f"Similar cases search returned {len(cases)} results")
                else:
                    self.log_warning("Similar cases search returned unexpected format")
            else:
                self.log_failure(f"Similar cases search failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Similar cases search failed", str(e))
            return False

        return True

    async def test_document_mode(self) -> bool:
        """Test document generation mode"""
        self.log_header("Testing Document Mode")

        # Test 1: List document types
        try:
            response = await self.client.get(f"{self.base_url}/documents/types")
            if response.status_code == 200:
                doc_types = response.json()
                if len(doc_types) > 0:
                    self.log_success(f"Document types listed: {len(doc_types)} types available")
                    self.log_info(f"  Types: {', '.join([dt['id'] for dt in doc_types[:3]])}")
                else:
                    self.log_warning("No document types available")
                    return False
            else:
                self.log_failure(f"Document types listing failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Document types listing failed", str(e))
            return False

        # Test 2: Get templates for a document type
        try:
            response = await self.client.get(
                f"{self.base_url}/documents/templates",
                params={"document_type": "nda", "language": "ka"}
            )
            if response.status_code == 200:
                templates = response.json()
                if len(templates) > 0:
                    self.log_success(f"Templates retrieved: {len(templates)} NDA templates")
                    template_id = templates[0]["id"]
                else:
                    self.log_warning("No templates available for NDA")
                    return False
            else:
                self.log_failure(f"Templates retrieval failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_failure("Templates retrieval failed", str(e))
            return False

        # Test 3: Generate document
        document_id = None
        try:
            generation_request = {
                "document_type": "nda",
                "template_id": template_id,
                "variables": {
                    "party_a_name": "შპს პირველი კომპანია",
                    "party_b_name": "შპს მეორე კომპანია",
                    "effective_date": "2024-12-10",
                    "confidentiality_period": "3"
                },
                "language": "ka",
                "include_legal_references": True,
                "format": "markdown"
            }
            response = await self.client.post(
                f"{self.base_url}/documents/generate",
                json=generation_request
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("document") and result.get("document_id"):
                    document_id = result["document_id"]
                    doc = result["document"]
                    self.log_success("Document generated successfully")
                    self.log_info(f"  Document ID: {document_id}")
                    self.log_info(f"  Format: {doc.get('format', 'N/A')}")
                    self.log_info(f"  Content length: {len(doc.get('content', ''))} chars")

                    # Verify content
                    content = doc.get("content", "")
                    if "შპს პირველი კომპანია" in content and "შპს მეორე კომპანია" in content:
                        self.log_success("Document contains expected variables")
                    else:
                        self.log_warning("Document missing expected variable substitutions")
                else:
                    self.log_failure("Generated document missing expected fields")
                    return False
            else:
                self.log_failure(f"Document generation failed with status {response.status_code}")
                error_detail = response.json().get("detail", "Unknown error")
                self.log_info(f"  Error: {error_detail}")
                return False
        except Exception as e:
            self.log_failure("Document generation request failed", str(e))
            return False

        # Test 4: Download document in different formats
        if document_id:
            for fmt in ["markdown", "docx"]:
                try:
                    response = await self.client.get(
                        f"{self.base_url}/documents/download/{document_id}",
                        params={"format": fmt}
                    )
                    if response.status_code == 200:
                        content = response.content
                        if len(content) > 0:
                            self.log_success(f"Document downloaded in {fmt.upper()} format ({len(content)} bytes)")
                        else:
                            self.log_warning(f"Downloaded {fmt.upper()} document is empty")
                    else:
                        self.log_failure(f"Document download ({fmt}) failed with status {response.status_code}")
                except Exception as e:
                    self.log_failure(f"Document download ({fmt}) request failed", str(e))

        return True

    async def test_integration_flow(self) -> bool:
        """Test complete integration flow across all modes"""
        self.log_header("Testing Integration Flow")

        # Scenario: User needs to create NDA and wants to understand tax implications
        self.log_info("Scenario: Creating NDA with tax consultation")

        # Step 1: Query tax information about contracts
        try:
            response = await self.client.post(
                f"{self.base_url}/tax/advice",
                json={
                    "question": "რა საგადასახადო შედეგები აქვს ხელშეკრულების გაფორმებას?",
                    "context": {"document_type": "nda"},
                    "language": "ka"
                }
            )
            if response.status_code == 200:
                self.log_success("Step 1: Tax consultation completed")
            else:
                self.log_failure("Step 1: Tax consultation failed")
                return False
        except Exception as e:
            self.log_failure("Step 1: Tax consultation request failed", str(e))
            return False

        # Step 2: Generate NDA document
        document_id = None
        try:
            response = await self.client.get(
                f"{self.base_url}/documents/templates",
                params={"document_type": "nda", "language": "ka"}
            )
            if response.status_code == 200 and len(response.json()) > 0:
                template_id = response.json()[0]["id"]

                gen_response = await self.client.post(
                    f"{self.base_url}/documents/generate",
                    json={
                        "document_type": "nda",
                        "template_id": template_id,
                        "variables": {
                            "party_a_name": "შპს კომპანია A",
                            "party_b_name": "შპს კომპანია B",
                            "effective_date": datetime.now().strftime("%Y-%m-%d")
                        },
                        "language": "ka",
                        "include_legal_references": True
                    }
                )
                if gen_response.status_code == 200:
                    document_id = gen_response.json().get("document_id")
                    self.log_success("Step 2: NDA document generated")
                else:
                    self.log_failure("Step 2: Document generation failed")
                    return False
            else:
                self.log_failure("Step 2: No NDA templates available")
                return False
        except Exception as e:
            self.log_failure("Step 2: Document generation request failed", str(e))
            return False

        # Step 3: Download the document
        if document_id:
            try:
                response = await self.client.get(
                    f"{self.base_url}/documents/download/{document_id}",
                    params={"format": "markdown"}
                )
                if response.status_code == 200:
                    self.log_success("Step 3: Document downloaded successfully")
                else:
                    self.log_failure("Step 3: Document download failed")
                    return False
            except Exception as e:
                self.log_failure("Step 3: Document download request failed", str(e))
                return False

        # Step 4: If dispute arises, analyze it
        try:
            response = await self.client.post(
                f"{self.base_url}/disputes/analyze",
                json={
                    "case_description": "ხელშეკრულების ფარგლებში წარმოიშვა დავა კონფიდენციალური ინფორმაციის გამჟღავნების შესახებ",
                    "taxpayer_info": {
                        "name": "შპს კომპანია A",
                        "tax_id": "123456789",
                        "type": " ltd"
                    },
                    "dispute_type": "contractual",
                    "language": "ka"
                }
            )
            if response.status_code == 200:
                self.log_success("Step 4: Dispute analysis completed")
            else:
                self.log_failure("Step 4: Dispute analysis failed")
                return False
        except Exception as e:
            self.log_failure("Step 4: Dispute analysis request failed", str(e))
            return False

        self.log_success("Integration flow completed successfully")
        return True

    async def test_error_handling(self) -> bool:
        """Test API error handling"""
        self.log_header("Testing Error Handling")

        # Test 1: Invalid document type
        try:
            response = await self.client.post(
                f"{self.base_url}/documents/generate",
                json={
                    "document_type": "invalid_type",
                    "template_id": "invalid",
                    "variables": {},
                    "language": "ka"
                }
            )
            if response.status_code in [400, 404, 422]:
                self.log_success("Invalid document type properly rejected")
            else:
                self.log_warning(f"Unexpected status code for invalid request: {response.status_code}")
        except Exception as e:
            self.log_failure("Error handling test failed", str(e))
            return False

        # Test 2: Missing required fields
        try:
            response = await self.client.post(
                f"{self.base_url}/tax/advice",
                json={"question": ""}  # Empty question
            )
            if response.status_code in [400, 422]:
                self.log_success("Empty question properly rejected")
            else:
                self.log_warning(f"Unexpected status code for empty question: {response.status_code}")
        except Exception as e:
            self.log_failure("Error handling test failed", str(e))
            return False

        # Test 3: Non-existent document download
        try:
            response = await self.client.get(
                f"{self.base_url}/documents/download/nonexistent-id"
            )
            if response.status_code == 404:
                self.log_success("Non-existent document properly returns 404")
            else:
                self.log_warning(f"Unexpected status code for non-existent document: {response.status_code}")
        except Exception as e:
            self.log_failure("Error handling test failed", str(e))
            return False

        return True

    def print_summary(self):
        """Print test summary"""
        self.log_header("Test Summary")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"Total tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.RESET}")
        print(f"Pass rate: {pass_rate:.1f}%\n")

        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}\n")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.RESET}\n")
            return False


async def main():
    """Main test execution"""
    print(f"\n{Colors.BOLD}Legal AI E2E Test Suite{Colors.RESET}")
    print(f"Testing API at: {BASE_URL}\n")

    runner = E2ETestRunner()

    try:
        # Health check
        if not await runner.test_health_check():
            print(f"\n{Colors.RED}API is not healthy. Please start the backend server.{Colors.RESET}")
            print(f"Run: cd backend && uvicorn app.main:app --reload\n")
            return 1

        # Run all test suites
        await runner.test_tax_mode()
        await runner.test_dispute_mode()
        await runner.test_document_mode()
        await runner.test_integration_flow()
        await runner.test_error_handling()

        # Print summary
        success = runner.print_summary()

        return 0 if success else 1

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}\n")
        return 1
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
