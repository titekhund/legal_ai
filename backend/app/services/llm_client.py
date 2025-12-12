"""
LLM client for interacting with language models (Gemini and Claude)
"""
import asyncio
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from app.core import (
    LLMError,
    RateLimitError,
    get_logger,
    get_settings,
    log_error,
    log_llm_request,
)

logger = get_logger(__name__)


# ============================================================================
# Abstract Base Class
# ============================================================================


class LLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[Any] = None
    ) -> str:
        """
        Generate text response from prompt

        Args:
            prompt: Input prompt
            context: Optional context information

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def generate_with_file(
        self,
        prompt: str,
        file_ref: Any
    ) -> str:
        """
        Generate text response with file context

        Args:
            prompt: Input prompt
            file_ref: File reference (path or uploaded file)

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model name being used

        Returns:
            Model name string
        """
        pass


# ============================================================================
# Gemini Client Implementation
# ============================================================================


class GeminiClient(LLMClient):
    """Google Gemini client implementation"""

    # Model preferences (in order)
    PREFERRED_MODELS = [
        "gemini-2.0-flash-exp",
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]

    # Generation configuration
    GENERATION_CONFIG = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0
    MAX_RETRY_DELAY = 10.0

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Gemini client

        Args:
            api_key: Gemini API key (defaults to settings)
            model_name: Specific model name (defaults to auto-selection)
        """
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Select model
        self.model_name = model_name or self._select_best_model()
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.GENERATION_CONFIG
        )

        # File cache for uploaded files
        self._file_cache: Dict[str, Any] = {}

        logger.info(f"Initialized GeminiClient with model: {self.model_name}")

    def _select_best_model(self) -> str:
        """
        Select the best available model

        Returns:
            Model name
        """
        try:
            available_models = [m.name for m in genai.list_models()]

            # Try preferred models in order
            for model in self.PREFERRED_MODELS:
                # Models are returned as 'models/gemini-...'
                full_name = f"models/{model}"
                if full_name in available_models:
                    logger.info(f"Selected model: {model}")
                    return model

            # Fallback to first available model
            if available_models:
                fallback = available_models[0].replace("models/", "")
                logger.warning(f"Using fallback model: {fallback}")
                return fallback

            # Last resort
            logger.warning("No models found, using default: gemini-2.5-flash")
            return "gemini-2.5-flash"

        except Exception as e:
            logger.warning(f"Error listing models: {e}, using default")
            return "gemini-2.5-flash"

    async def _retry_with_backoff(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RateLimitError: If max retries exceeded
            LLMError: If other error occurs
        """
        last_error = None
        delay = self.INITIAL_RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a rate limit error
                if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning(
                            f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, self.MAX_RETRY_DELAY)
                        continue
                    else:
                        raise RateLimitError(
                            message=f"Rate limit exceeded after {self.MAX_RETRIES} retries",
                            details={"error": str(e)}
                        )
                else:
                    # Non-rate-limit error, don't retry
                    raise LLMError(
                        message=f"Gemini API error: {str(e)}",
                        details={"error": str(e), "attempt": attempt + 1}
                    )

        # Should not reach here, but just in case
        raise LLMError(
            message=f"Failed after {self.MAX_RETRIES} retries",
            details={"last_error": str(last_error)}
        )

    async def generate(
        self,
        prompt: str,
        context: Optional[Any] = None
    ) -> str:
        """
        Generate text response from prompt

        Args:
            prompt: Input prompt
            context: Optional context information

        Returns:
            Generated text response
        """
        start_time = time.time()

        try:
            # Prepare the full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\n{prompt}"

            # Generate content with retry logic
            async def _generate():
                return self.model.generate_content(full_prompt)

            response: GenerateContentResponse = await self._retry_with_backoff(_generate)

            # Extract response text
            response_text = response.text

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log the request
            prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

            log_llm_request(
                logger,
                provider="gemini",
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                duration_ms=duration_ms
            )

            return response_text

        except (RateLimitError, LLMError):
            raise
        except Exception as e:
            log_error(logger, e, {"prompt_length": len(prompt)})
            raise LLMError(
                message=f"Unexpected error in Gemini generate: {str(e)}",
                details={"error": str(e)}
            )

    async def generate_with_file(
        self,
        prompt: str,
        file_ref: Any
    ) -> str:
        """
        Generate text response with file context

        Args:
            prompt: Input prompt
            file_ref: File path or uploaded file reference

        Returns:
            Generated text response
        """
        start_time = time.time()

        try:
            # Handle file reference
            if isinstance(file_ref, (str, Path)):
                file_path = str(file_ref)

                # Check cache
                if file_path in self._file_cache:
                    logger.info(f"Using cached file upload: {file_path}")
                    uploaded_file = self._file_cache[file_path]
                else:
                    # Upload file
                    logger.info(f"Uploading file: {file_path}")
                    uploaded_file = genai.upload_file(file_path)
                    self._file_cache[file_path] = uploaded_file
                    logger.info(f"File uploaded successfully: {uploaded_file.name}")
            else:
                # Assume it's already an uploaded file
                uploaded_file = file_ref

            # Generate content with file
            async def _generate():
                return self.model.generate_content([uploaded_file, prompt])

            response: GenerateContentResponse = await self._retry_with_backoff(_generate)

            # Extract response text
            response_text = response.text

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log the request
            prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

            log_llm_request(
                logger,
                provider="gemini",
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                duration_ms=duration_ms
            )

            return response_text

        except (RateLimitError, LLMError):
            raise
        except Exception as e:
            log_error(logger, e, {"prompt_length": len(prompt), "file_ref": str(file_ref)})
            raise LLMError(
                message=f"Unexpected error in Gemini generate_with_file: {str(e)}",
                details={"error": str(e)}
            )

    def get_model_name(self) -> str:
        """Get the model name being used"""
        return self.model_name

    def clear_file_cache(self) -> None:
        """Clear the file upload cache"""
        self._file_cache.clear()
        logger.info("File cache cleared")


# ============================================================================
# Claude Client Implementation
# ============================================================================


class ClaudeClient(LLMClient):
    """Anthropic Claude client implementation (fallback)"""

    # Model configuration
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    # Generation configuration
    MAX_TOKENS = 8192
    TEMPERATURE = 0.1

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0
    MAX_RETRY_DELAY = 10.0

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Claude client

        Args:
            api_key: Claude API key (defaults to settings)
            model_name: Specific model name (defaults to DEFAULT_MODEL)
        """
        settings = get_settings()
        self.api_key = api_key or settings.claude_api_key

        if not self.api_key:
            raise LLMError(
                message="Claude API key not configured",
                details={"config_key": "CLAUDE_API_KEY"}
            )

        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.model_name = model_name or self.DEFAULT_MODEL

        logger.info(f"Initialized ClaudeClient with model: {self.model_name}")

    async def _retry_with_backoff(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RateLimitError: If max retries exceeded
            LLMError: If other error occurs
        """
        last_error = None
        delay = self.INITIAL_RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except anthropic.RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.MAX_RETRY_DELAY)
                    continue
                else:
                    raise RateLimitError(
                        message=f"Rate limit exceeded after {self.MAX_RETRIES} retries",
                        details={"error": str(e)}
                    )
            except anthropic.APIError as e:
                log_error(logger, e, {"attempt": attempt + 1})
                raise LLMError(
                    message=f"Claude API error: {str(e)}",
                    details={"error": str(e), "attempt": attempt + 1}
                )
            except Exception as e:
                log_error(logger, e, {"attempt": attempt + 1})
                raise LLMError(
                    message=f"Unexpected error: {str(e)}",
                    details={"error": str(e), "attempt": attempt + 1}
                )

        # Should not reach here
        raise LLMError(
            message=f"Failed after {self.MAX_RETRIES} retries",
            details={"last_error": str(last_error)}
        )

    async def generate(
        self,
        prompt: str,
        context: Optional[Any] = None
    ) -> str:
        """
        Generate text response from prompt

        Args:
            prompt: Input prompt
            context: Optional context information

        Returns:
            Generated text response
        """
        start_time = time.time()

        try:
            # Prepare messages
            user_message = prompt
            if context:
                user_message = f"{context}\n\n{prompt}"

            # Generate with retry logic
            async def _generate():
                return await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.MAX_TOKENS,
                    temperature=self.TEMPERATURE,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )

            response = await self._retry_with_backoff(_generate)

            # Extract response text
            response_text = response.content[0].text

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log the request
            log_llm_request(
                logger,
                provider="claude",
                model=self.model_name,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                duration_ms=duration_ms
            )

            return response_text

        except (RateLimitError, LLMError):
            raise
        except Exception as e:
            log_error(logger, e, {"prompt_length": len(prompt)})
            raise LLMError(
                message=f"Unexpected error in Claude generate: {str(e)}",
                details={"error": str(e)}
            )

    async def generate_with_file(
        self,
        prompt: str,
        file_ref: Any
    ) -> str:
        """
        Generate text response with file context

        Note: Claude doesn't support direct file upload like Gemini.
        The file_ref should be the extracted text content from the file.

        Args:
            prompt: Input prompt
            file_ref: Text content extracted from file

        Returns:
            Generated text response
        """
        start_time = time.time()

        try:
            # For Claude, file_ref should be the text content
            if isinstance(file_ref, (str, Path)):
                # If it's a path, read the file
                with open(file_ref, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            else:
                # Assume it's already text content
                file_content = str(file_ref)

            # Create context message with file content
            context_message = f"Here is the document content:\n\n{file_content}\n\n"

            # Generate with retry logic
            async def _generate():
                return await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.MAX_TOKENS,
                    temperature=self.TEMPERATURE,
                    messages=[
                        {"role": "user", "content": context_message + prompt}
                    ]
                )

            response = await self._retry_with_backoff(_generate)

            # Extract response text
            response_text = response.content[0].text

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log the request
            log_llm_request(
                logger,
                provider="claude",
                model=self.model_name,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                duration_ms=duration_ms
            )

            return response_text

        except (RateLimitError, LLMError):
            raise
        except Exception as e:
            log_error(logger, e, {"prompt_length": len(prompt)})
            raise LLMError(
                message=f"Unexpected error in Claude generate_with_file: {str(e)}",
                details={"error": str(e)}
            )

    def get_model_name(self) -> str:
        """Get the model name being used"""
        return self.model_name


# ============================================================================
# LLM Client Factory
# ============================================================================


class LLMClientFactory:
    """Factory for creating and managing LLM clients"""

    _primary_client: Optional[GeminiClient] = None
    _fallback_client: Optional[ClaudeClient] = None

    @classmethod
    def get_primary_client(cls) -> GeminiClient:
        """
        Get the primary LLM client (Gemini)

        Returns:
            GeminiClient instance
        """
        if cls._primary_client is None:
            cls._primary_client = GeminiClient()
        return cls._primary_client

    @classmethod
    def get_fallback_client(cls) -> ClaudeClient:
        """
        Get the fallback LLM client (Claude)

        Returns:
            ClaudeClient instance

        Raises:
            LLMError: If Claude API key not configured
        """
        if cls._fallback_client is None:
            cls._fallback_client = ClaudeClient()
        return cls._fallback_client

    @classmethod
    async def get_client_with_fallback(cls) -> LLMClient:
        """
        Get LLM client with automatic fallback

        Tries to use Gemini first, falls back to Claude if error occurs.

        Returns:
            LLMClient instance (Gemini or Claude)
        """
        try:
            # Try to get primary client
            client = cls.get_primary_client()

            # Test with a simple prompt to ensure it works
            logger.info("Testing primary client (Gemini)...")
            await client.generate("test", context=None)

            logger.info("Primary client (Gemini) is working")
            return client

        except Exception as e:
            logger.warning(f"Primary client (Gemini) failed: {e}")
            logger.info("Falling back to Claude client...")

            try:
                client = cls.get_fallback_client()
                logger.info("Using fallback client (Claude)")
                return client
            except Exception as fallback_error:
                logger.error(f"Fallback client (Claude) also failed: {fallback_error}")
                raise LLMError(
                    message="Both primary and fallback LLM clients failed",
                    details={
                        "primary_error": str(e),
                        "fallback_error": str(fallback_error)
                    }
                )

    @classmethod
    def reset(cls) -> None:
        """Reset the factory (clear cached clients)"""
        cls._primary_client = None
        cls._fallback_client = None
        logger.info("LLMClientFactory reset")
