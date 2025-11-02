"""Vertex AI integration service using Google GenAI SDK.

This module handles communication with Google's Vertex AI Gemini API for
character sheet generation using structured output with the new GenAI SDK.
"""

import json
import os
import time
from typing import Any, Dict

from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch

from app.config import settings
from app.core.exceptions import ConfigurationError, LLMGenerationError
from app.core.logger import get_logger
from app.core.utils import convert_openapi_to_genai_schema

logger = get_logger(__name__)


class VertexAIClient:
    """Client for interacting with Vertex AI Gemini API using new GenAI SDK.

    This service handles initialization of Vertex AI, model configuration,
    and generation of character sheets using structured JSON output.
    """

    def __init__(self):
        """Initialize Vertex AI client and model.

        Raises:
            ConfigurationError: If Vertex AI initialization fails
        """
        try:
            logger.info("Initializing Vertex AI client with Google GenAI SDK")

            # Set credentials environment variable if configured in settings
            # but not already set in the OS environment
            if settings.google_application_credentials:
                if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                    # Convert to string if it's a Path object
                    creds_path = str(settings.google_application_credentials)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                    logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS from config: {creds_path}")
                else:
                    logger.info("Using existing GOOGLE_APPLICATION_CREDENTIALS from environment")

            # Initialize GenAI client with Vertex AI
            self.client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location
            )

            logger.info(
                f"Vertex AI client initialized successfully with model: {settings.gemini_model}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise ConfigurationError(
                f"Failed to initialize Vertex AI client: {str(e)}. "
                f"Please check your Google Cloud configuration and credentials."
            )

    def generate_character_sheet(
        self,
        prompt: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate character sheet using Gemini API with structured output.

        This method sends a prompt to the Gemini API and enforces JSON output
        that conforms to the provided schema.

        Args:
            prompt: Complete prompt for character generation
            schema: OpenAPI 3.0 compatible JSON schema for output structure

        Returns:
            Generated character sheet as a dictionary

        Raises:
            LLMGenerationError: If generation fails

        Example:
            >>> client = VertexAIClient()
            >>> result = client.generate_character_sheet(prompt, schema)
        """
        logger.info("Starting character sheet generation")
        logger.debug(f"Prompt length: {len(prompt)} characters")

        try:
            # Convert OpenAPI schema to GenAI format (uppercase types)
            genai_schema = convert_openapi_to_genai_schema(schema)
            logger.debug("Converted schema to GenAI format")

            # Configure generation with structured output
            generation_config = GenerateContentConfig(
                temperature=settings.temperature,
                max_output_tokens=settings.max_output_tokens,
                response_mime_type="application/json",
                response_schema=genai_schema
            )

            logger.debug(
                f"Generation config: temperature={settings.temperature}, "
                f"max_tokens={settings.max_output_tokens}"
            )

            # Generate content with retry logic
            response = self._generate_with_retry(prompt, generation_config)

            # Parse JSON response
            try:
                character_data = json.loads(response.text)
                logger.info("Character sheet generated successfully")
                return character_data

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in LLM response: {str(e)}")
                logger.error(f"Response text preview: {response.text[:1000]}")
                raise LLMGenerationError(
                    f"LLM returned invalid JSON: {str(e)}. Response: {response.text[:500]}"
                )

        except LLMGenerationError:
            raise  # Re-raise LLM errors as-is

        except Exception as e:
            logger.error(f"Unexpected error during generation: {str(e)}")
            logger.exception("Full error traceback:")
            raise LLMGenerationError(f"Character generation failed: {str(e)}")

    def _generate_with_retry(
        self,
        prompt: str,
        generation_config: GenerateContentConfig,
        max_retries: int = None
    ):
        """Generate content with retry logic for transient failures.

        Args:
            prompt: Prompt text
            generation_config: Generation configuration
            max_retries: Maximum retry attempts (uses settings.max_retries if None)

        Returns:
            Generation response

        Raises:
            LLMGenerationError: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = settings.max_retries

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries + 1}")

                # Use the new GenAI SDK's generate_content method
                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=generation_config
                )

                # Check if response is valid
                if not response or not response.text:
                    raise LLMGenerationError("Empty response from LLM")

                logger.debug(f"Generation successful on attempt {attempt + 1}")
                return response

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Generation attempt {attempt + 1} failed: {str(e)}"
                )

                # If not the last attempt, wait before retrying
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        # All retries failed
        logger.error(f"All {max_retries + 1} generation attempts failed")
        raise LLMGenerationError(
            f"Failed after {max_retries + 1} attempts. Last error: {str(last_error)}"
        )

    def test_connection(self) -> bool:
        """Test connection to Vertex AI by generating a simple response.

        Returns:
            True if connection is working

        Raises:
            LLMGenerationError: If connection test fails

        Example:
            >>> client = VertexAIClient()
            >>> if client.test_connection():
            ...     print("Connection OK")
        """
        try:
            logger.info("Testing Vertex AI connection")

            test_prompt = "Say 'OK' if you can read this."

            generation_config = GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10
            )

            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=test_prompt,
                config=generation_config
            )

            if response and response.text:
                logger.info("Vertex AI connection test successful")
                return True
            else:
                logger.error("Vertex AI connection test failed: Empty response")
                return False

        except Exception as e:
            logger.error(f"Vertex AI connection test failed: {str(e)}")
            raise LLMGenerationError(f"Connection test failed: {str(e)}")
