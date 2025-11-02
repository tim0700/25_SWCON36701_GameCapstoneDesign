"""API middleware and error handlers.

This module defines FastAPI exception handlers for custom exceptions,
converting them to appropriate HTTP responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import (
    ConfigurationError,
    LLMGenerationError,
    StorageError,
    TemplateError,
    ValidationError,
)
from app.core.logger import get_logger
from app.models.schemas import ErrorResponse

logger = get_logger(__name__)


async def validation_error_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """Handle custom ValidationError exceptions.

    Args:
        request: The incoming request
        exc: ValidationError exception

    Returns:
        JSON response with 422 status code
    """
    logger.error(f"Validation error: {str(exc)}")

    error_response = ErrorResponse(
        error_type="validation_error",
        error_message=str(exc),
        details={"path": request.url.path}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors from request models.

    Args:
        request: The incoming request
        exc: Pydantic ValidationError exception

    Returns:
        JSON response with 422 status code
    """
    logger.error(f"Pydantic validation error: {str(exc)}")

    # Extract error details from Pydantic
    error_details = {
        "validation_errors": exc.errors(),
        "path": request.url.path
    }

    error_response = ErrorResponse(
        error_type="request_validation_error",
        error_message="Invalid request data",
        details=error_details
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def llm_generation_error_handler(
    request: Request,
    exc: LLMGenerationError
) -> JSONResponse:
    """Handle LLM generation errors.

    Args:
        request: The incoming request
        exc: LLMGenerationError exception

    Returns:
        JSON response with 503 status code
    """
    logger.error(f"LLM generation error: {str(exc)}")

    error_response = ErrorResponse(
        error_type="llm_generation_error",
        error_message="Failed to generate character sheet from LLM",
        details={
            "reason": str(exc),
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump()
    )


async def storage_error_handler(
    request: Request,
    exc: StorageError
) -> JSONResponse:
    """Handle file storage errors.

    Args:
        request: The incoming request
        exc: StorageError exception

    Returns:
        JSON response with 500 status code
    """
    logger.error(f"Storage error: {str(exc)}")

    error_response = ErrorResponse(
        error_type="storage_error",
        error_message="Failed to save character sheet to storage",
        details={
            "reason": str(exc),
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


async def template_error_handler(
    request: Request,
    exc: TemplateError
) -> JSONResponse:
    """Handle template loading errors.

    Args:
        request: The incoming request
        exc: TemplateError exception

    Returns:
        JSON response with 500 status code
    """
    logger.error(f"Template error: {str(exc)}")

    error_response = ErrorResponse(
        error_type="template_error",
        error_message="Failed to load required templates",
        details={
            "reason": str(exc),
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


async def configuration_error_handler(
    request: Request,
    exc: ConfigurationError
) -> JSONResponse:
    """Handle configuration errors.

    Args:
        request: The incoming request
        exc: ConfigurationError exception

    Returns:
        JSON response with 500 status code
    """
    logger.error(f"Configuration error: {str(exc)}")

    error_response = ErrorResponse(
        error_type="configuration_error",
        error_message="Application configuration error",
        details={
            "reason": str(exc),
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: The incoming request
        exc: Any unhandled exception

    Returns:
        JSON response with 500 status code
    """
    logger.exception(f"Unhandled exception: {str(exc)}")

    error_response = ErrorResponse(
        error_type="internal_server_error",
        error_message="An unexpected error occurred",
        details={
            "exception_type": type(exc).__name__,
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_error_handler)
    app.add_exception_handler(LLMGenerationError, llm_generation_error_handler)
    app.add_exception_handler(StorageError, storage_error_handler)
    app.add_exception_handler(TemplateError, template_error_handler)
    app.add_exception_handler(ConfigurationError, configuration_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
