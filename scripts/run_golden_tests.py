#!/usr/bin/env python3
"""
Golden Test Runner for Legal AI Tax Code Assistant

This script runs the golden test cases defined in docs/golden_tests.yaml
against the running API to verify system quality.

Usage:
    python scripts/run_golden_tests.py
    python scripts/run_golden_tests.py --api-url http://localhost:8000
    python scripts/run_golden_tests.py --output results.json
    python scripts/run_golden_tests.py --verbose
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import httpx
import yaml


class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class GoldenTestRunner:
    """Runner for golden test cases"""

    def __init__(self, api_url: str, timeout: int = 30, verbose: bool = False):
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.verbose = verbose
        self.results = []

    async def run_all_tests(self, test_file: Path) -> Dict[str, Any]:
        """Run all tests from the golden test file"""
        with open(test_file, 'r', encoding='utf-8') as f:
            tests = yaml.safe_load(f)

        print(f"\n{Colors.BOLD}Running Golden Tests{Colors.RESET}")
        print(f"API URL: {self.api_url}")
        print(f"Test file: {test_file}")
        print("-" * 80)

        results = {
            "timestamp": datetime.now().isoformat(),
            "api_url": self.api_url,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "test_results": []
        }

        # Run tax code tests
        if "tax_code_tests" in tests:
            print(f"\n{Colors.BLUE}Tax Code Tests{Colors.RESET}")
            for test in tests["tax_code_tests"]:
                result = await self.run_test(test, test_type="tax_code")
                results["test_results"].append(result)
                results["total_tests"] += 1

                if result["status"] == "PASS":
                    results["passed"] += 1
                    print(f"  {Colors.GREEN}{Colors.RESET} {test['id']}: {test['question'][:60]}...")
                elif result["status"] == "FAIL":
                    results["failed"] += 1
                    print(f"  {Colors.RED}{Colors.RESET} {test['id']}: {test['question'][:60]}...")
                    if self.verbose:
                        for failure in result["failures"]:
                            print(f"    - {Colors.YELLOW}{failure}{Colors.RESET}")
                else:
                    results["errors"] += 1
                    print(f"  {Colors.RED}E{Colors.RESET} {test['id']}: {test['question'][:60]}...")
                    if self.verbose and result.get("error"):
                        print(f"    - {Colors.RED}{result['error']}{Colors.RESET}")

        # Run edge case tests
        if "edge_cases" in tests:
            print(f"\n{Colors.BLUE}Edge Case Tests{Colors.RESET}")
            for test in tests["edge_cases"]:
                result = await self.run_test(test, test_type="edge_case")
                results["test_results"].append(result)
                results["total_tests"] += 1

                if result["status"] == "PASS":
                    results["passed"] += 1
                    print(f"  {Colors.GREEN}{Colors.RESET} {test['id']}: {test['question'][:60]}...")
                elif result["status"] == "FAIL":
                    results["failed"] += 1
                    print(f"  {Colors.RED}{Colors.RESET} {test['id']}: {test['question'][:60]}...")
                else:
                    results["errors"] += 1
                    print(f"  {Colors.RED}E{Colors.RESET} {test['id']}: {test['question'][:60]}...")

        return results

    async def run_test(self, test: Dict[str, Any], test_type: str) -> Dict[str, Any]:
        """Run a single test case"""
        result = {
            "test_id": test["id"],
            "test_type": test_type,
            "question": test["question"],
            "status": "PASS",
            "failures": [],
            "error": None,
            "response_time_ms": None,
            "api_response": None
        }

        try:
            # Send request to API
            start_time = datetime.now()
            response_data = await self.send_chat_request(test["question"])
            end_time = datetime.now()

            result["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
            result["api_response"] = response_data

            if self.verbose:
                print(f"\n{Colors.BOLD}Test: {test['id']}{Colors.RESET}")
                print(f"Question: {test['question']}")
                print(f"Response: {response_data.get('answer', '')[:200]}...")
                print(f"Response time: {result['response_time_ms']:.0f}ms")

            # Validate response based on test type
            if test_type == "tax_code":
                self.validate_tax_code_test(test, response_data, result)
            elif test_type == "edge_case":
                self.validate_edge_case_test(test, response_data, result)

            # Set overall status
            if result["failures"]:
                result["status"] = "FAIL"

        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)

        return result

    async def send_chat_request(self, question: str) -> Dict[str, Any]:
        """Send chat request to API"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/v1/chat",
                json={
                    "message": question,
                    "conversation_id": f"golden_test_{datetime.now().timestamp()}"
                }
            )

            if response.status_code != 200:
                raise Exception(f"API returned status code {response.status_code}: {response.text}")

            return response.json()

    def validate_tax_code_test(self, test: Dict[str, Any], response: Dict[str, Any], result: Dict[str, Any]):
        """Validate tax code test expectations"""
        answer = response.get("answer", "")
        sources = response.get("sources", [])

        # Check expected articles are cited
        if "expected_articles" in test:
            cited_articles = [s.get("article", "") for s in sources]

            for expected_article in test["expected_articles"]:
                # Check if the article appears in any cited article (handles "166" matching "166", "166.1", etc.)
                found = any(expected_article in article or article == expected_article for article in cited_articles)

                if not found:
                    result["failures"].append(
                        f"Expected article {expected_article} not found in citations. "
                        f"Got: {cited_articles}"
                    )

        # Check expected keywords in answer
        if "expected_contains" in test:
            for keyword in test["expected_contains"]:
                if keyword.lower() not in answer.lower():
                    result["failures"].append(
                        f"Expected keyword '{keyword}' not found in answer"
                    )

    def validate_edge_case_test(self, test: Dict[str, Any], response: Dict[str, Any], result: Dict[str, Any]):
        """Validate edge case test expectations"""
        answer = response.get("answer", "")

        # Check if response should mention something
        if "should_mention" in test:
            if test["should_mention"].lower() not in answer.lower():
                result["failures"].append(
                    f"Expected mention of '{test['should_mention']}' not found in answer"
                )

        # Check if system should respond
        if test.get("should_respond", False):
            if not answer or len(answer.strip()) == 0:
                result["failures"].append("Expected a response but got empty answer")

        # Check if system should not error
        if test.get("should_not_error", False):
            if "error" in response or response.get("status") == "error":
                result["failures"].append("Expected no error but got error response")

    def print_summary(self, results: Dict[str, Any]):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
        print("=" * 80)

        print(f"Total Tests: {results['total_tests']}")
        print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {results['failed']}{Colors.RESET}")
        print(f"{Colors.RED}Errors: {results['errors']}{Colors.RESET}")

        if results['total_tests'] > 0:
            pass_rate = (results['passed'] / results['total_tests']) * 100
            print(f"\nPass Rate: {pass_rate:.1f}%")

            if pass_rate == 100:
                print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed! {Colors.RESET}")
            elif pass_rate >= 80:
                print(f"\n{Colors.YELLOW}Most tests passed, but some issues remain.{Colors.RESET}")
            else:
                print(f"\n{Colors.RED}Many tests failed. Please review the results.{Colors.RESET}")

    def save_results(self, results: Dict[str, Any], output_file: Path):
        """Save results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n{Colors.GREEN}Results saved to: {output_file}{Colors.RESET}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run golden tests for Legal AI system")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--test-file",
        default="docs/golden_tests.yaml",
        help="Path to golden tests YAML file (default: docs/golden_tests.yaml)"
    )
    parser.add_argument(
        "--output",
        default="test_results.json",
        help="Output file for results (default: test_results.json)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    # Check if test file exists
    test_file = Path(args.test_file)
    if not test_file.exists():
        print(f"{Colors.RED}Error: Test file not found: {test_file}{Colors.RESET}")
        sys.exit(1)

    # Create runner and run tests
    runner = GoldenTestRunner(
        api_url=args.api_url,
        timeout=args.timeout,
        verbose=args.verbose
    )

    try:
        results = await runner.run_all_tests(test_file)
        runner.print_summary(results)
        runner.save_results(results, Path(args.output))

        # Exit with non-zero code if tests failed
        if results["failed"] > 0 or results["errors"] > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
