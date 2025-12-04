"""Custom exception classes for the Character Sheet Generator.

This module defines a hierarchy of custom exceptions used throughout the application
to provide clear error handling and reporting.
"""


class CharacterGeneratorError(Exception):
    """Base exception for all custom errors in the application."""

    pass


class ConfigurationError(CharacterGeneratorError):
    """Raised when there are configuration or environment setup errors.

    Examples:
        - Missing environment variables
        - Invalid configuration values
        - Google Cloud credentials not found
    """

    pass


class TemplateError(CharacterGeneratorError):
    """Raised when template loading or parsing fails.

    Examples:
        - Template file not found
        - Invalid template format
        - JSON schema parsing error
    """

    pass


class LLMGenerationError(CharacterGeneratorError):
    """Raised when Vertex AI API call failures occur.

    Examples:
        - API timeout
        - Authentication failure
        - Model not available
        - Rate limiting
    """

    pass


class ValidationError(CharacterGeneratorError):
    """Raised when character sheet validation fails.

    Examples:
        - Missing required fields
        - Invalid field values
        - Business logic violations
    """

    pass


class StorageError(CharacterGeneratorError):
    """Raised when file storage operation failures occur.

    Examples:
        - Permission denied
        - Disk full
        - Invalid file path
        - File already exists
    """

    pass
