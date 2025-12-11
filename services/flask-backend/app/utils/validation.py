"""Validation utilities for API request validation using Pydantic schemas.

This module provides decorators for validating JSON request bodies and query
parameters using Pydantic v2 schemas. It handles validation errors gracefully
and returns detailed error messages to the client.
"""

from functools import wraps
from typing import Type

from flask import Request, jsonify, request
from pydantic import BaseModel, ValidationError


def validate_json(schema: Type[BaseModel]):
    """Decorator to validate JSON request body against a Pydantic schema.

    Args:
        schema: Pydantic BaseModel class to validate against

    Returns:
        Decorated function with validated_data kwarg added

    Example:
        @app.route("/api/users", methods=["POST"])
        @validate_json(CreateUserRequest)
        def create_user(validated_data: CreateUserRequest):
            # Access validated_data.email, validated_data.password, etc.
            ...

    Error Response Format:
        {
            "error": "Validation failed",
            "details": [
                {
                    "field": "password",
                    "message": "Password must contain at least one uppercase letter",
                    "type": "value_error"
                }
            ]
        }
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Get JSON data from request
                data = request.get_json()

                # Handle missing request body
                if data is None:
                    return (
                        jsonify(
                            {
                                "error": "Request body required",
                                "details": [
                                    {
                                        "field": "body",
                                        "message": "JSON request body is required",
                                        "type": "missing_body",
                                    }
                                ],
                            }
                        ),
                        400,
                    )

                # Validate data against schema
                validated_data = schema(**data)

                # Add validated data to kwargs
                kwargs["validated_data"] = validated_data

                # Call the original function
                return f(*args, **kwargs)

            except ValidationError as e:
                # Format validation errors for client
                errors = []
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    errors.append(
                        {
                            "field": field_path,
                            "message": error["msg"],
                            "type": error["type"],
                        }
                    )

                return (
                    jsonify(
                        {
                            "error": "Validation failed",
                            "details": errors,
                        }
                    ),
                    400,
                )

            except Exception as e:
                # Handle unexpected errors
                return (
                    jsonify(
                        {
                            "error": "Invalid request",
                            "details": [
                                {
                                    "field": "unknown",
                                    "message": str(e),
                                    "type": "unexpected_error",
                                }
                            ],
                        }
                    ),
                    400,
                )

        return wrapper

    return decorator


def validate_query(schema: Type[BaseModel]):
    """Decorator to validate query parameters against a Pydantic schema.

    Args:
        schema: Pydantic BaseModel class to validate against

    Returns:
        Decorated function with validated_query kwarg added

    Example:
        @app.route("/api/users", methods=["GET"])
        @validate_query(PaginationParams)
        def list_users(validated_query: PaginationParams):
            # Access validated_query.page, validated_query.per_page, etc.
            ...

    Error Response Format:
        {
            "error": "Validation failed",
            "details": [
                {
                    "field": "page",
                    "message": "Input should be greater than or equal to 1",
                    "type": "greater_than_equal"
                }
            ]
        }
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Get query parameters from request
                query_params = request.args.to_dict()

                # Convert numeric strings to appropriate types
                # This is necessary because Flask query params are always strings
                for key, value in query_params.items():
                    # Try to convert to int
                    if value.isdigit():
                        query_params[key] = int(value)
                    # Try to convert to float
                    elif value.replace(".", "", 1).isdigit():
                        query_params[key] = float(value)
                    # Try to convert to boolean
                    elif value.lower() in ["true", "false"]:
                        query_params[key] = value.lower() == "true"

                # Validate query params against schema
                validated_query = schema(**query_params)

                # Add validated query to kwargs
                kwargs["validated_query"] = validated_query

                # Call the original function
                return f(*args, **kwargs)

            except ValidationError as e:
                # Format validation errors for client
                errors = []
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    errors.append(
                        {
                            "field": field_path,
                            "message": error["msg"],
                            "type": error["type"],
                        }
                    )

                return (
                    jsonify(
                        {
                            "error": "Validation failed",
                            "details": errors,
                        }
                    ),
                    400,
                )

            except Exception as e:
                # Handle unexpected errors
                return (
                    jsonify(
                        {
                            "error": "Invalid query parameters",
                            "details": [
                                {
                                    "field": "unknown",
                                    "message": str(e),
                                    "type": "unexpected_error",
                                }
                            ],
                        }
                    ),
                    400,
                )

        return wrapper

    return decorator


def validate_form(schema: Type[BaseModel]):
    """Decorator to validate form data against a Pydantic schema.

    Args:
        schema: Pydantic BaseModel class to validate against

    Returns:
        Decorated function with validated_form kwarg added

    Example:
        @app.route("/api/upload", methods=["POST"])
        @validate_form(UploadFormRequest)
        def upload_file(validated_form: UploadFormRequest):
            # Access validated_form fields
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Get form data from request
                form_data = request.form.to_dict()

                # Handle missing form data
                if not form_data:
                    return (
                        jsonify(
                            {
                                "error": "Form data required",
                                "details": [
                                    {
                                        "field": "body",
                                        "message": "Form data is required",
                                        "type": "missing_form",
                                    }
                                ],
                            }
                        ),
                        400,
                    )

                # Validate form data against schema
                validated_form = schema(**form_data)

                # Add validated form to kwargs
                kwargs["validated_form"] = validated_form

                # Call the original function
                return f(*args, **kwargs)

            except ValidationError as e:
                # Format validation errors for client
                errors = []
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    errors.append(
                        {
                            "field": field_path,
                            "message": error["msg"],
                            "type": error["type"],
                        }
                    )

                return (
                    jsonify(
                        {
                            "error": "Validation failed",
                            "details": errors,
                        }
                    ),
                    400,
                )

            except Exception as e:
                # Handle unexpected errors
                return (
                    jsonify(
                        {
                            "error": "Invalid form data",
                            "details": [
                                {
                                    "field": "unknown",
                                    "message": str(e),
                                    "type": "unexpected_error",
                                }
                            ],
                        }
                    ),
                    400,
                )

        return wrapper

    return decorator


__all__ = ["validate_json", "validate_query", "validate_form"]
