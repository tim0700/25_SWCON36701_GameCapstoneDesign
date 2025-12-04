"""Core utility functions.

This module provides helper functions for schema conversion and other common operations.
"""

from typing import Any, Dict


def convert_openapi_to_genai_schema(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAPI 3.0 schema format to Google GenAI schema format.

    The new Google GenAI SDK uses uppercase type names (STRING, OBJECT, ARRAY)
    instead of lowercase (string, object, array) used in OpenAPI.

    Args:
        openapi_schema: OpenAPI 3.0 compatible JSON schema

    Returns:
        Schema in Google GenAI format

    Example:
        >>> openapi = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> genai = convert_openapi_to_genai_schema(openapi)
        >>> genai["type"]
        'OBJECT'
    """
    def convert_type(schema_type: str) -> str:
        """Convert type from lowercase to uppercase format."""
        type_mapping = {
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT"
        }
        return type_mapping.get(schema_type, schema_type.upper())

    def convert_schema_recursive(schema: Any) -> Any:
        """Recursively convert schema structure."""
        if not isinstance(schema, dict):
            return schema

        converted = {}

        for key, value in schema.items():
            if key == "type":
                # Convert type to uppercase
                converted[key] = convert_type(value)
            elif key == "properties":
                # Recursively convert nested properties
                converted[key] = {
                    prop_name: convert_schema_recursive(prop_value)
                    for prop_name, prop_value in value.items()
                }
            elif key == "items":
                # Recursively convert array items schema
                converted[key] = convert_schema_recursive(value)
            else:
                # Keep other fields as-is
                converted[key] = value

        return converted

    return convert_schema_recursive(openapi_schema)
