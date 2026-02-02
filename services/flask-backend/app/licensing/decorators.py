"""License decorators for gating features."""

import logging
from functools import wraps
from typing import Callable, Optional

from flask import jsonify

from . import get_client
from .client import FeatureNotAvailableError

logger = logging.getLogger(__name__)


def license_required(minimum_tier: Optional[str] = None) -> Callable:
    """
    Decorator to require a minimum license tier for an endpoint.

    Args:
        minimum_tier: Minimum tier required (e.g., 'professional', 'enterprise')
                     If None, just requires valid license

    Returns:
        Decorated function

    Raises:
        FeatureNotAvailableError: If license requirement not met
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = get_client()

            if client is None:
                logger.warning(
                    f"License required for {func.__name__} but client not initialized"
                )
                return (
                    jsonify(
                        {
                            "error": "License not configured",
                            "message": "Feature requires valid license",
                        }
                    ),
                    403,
                )

            try:
                # If minimum tier is specified, check it
                if minimum_tier:
                    # This would require fetching the current tier from license server
                    # For now, we check if any feature is available as a basic check
                    features = client.get_all_features()
                    if not features:
                        raise FeatureNotAvailableError(f"tier:{minimum_tier}")

                # Proceed to the actual endpoint
                return func(*args, **kwargs)

            except FeatureNotAvailableError as e:
                logger.warning(f"License requirement failed for {func.__name__}: {e}")
                return (
                    jsonify(
                        {"error": "License requirement not met", "message": str(e)}
                    ),
                    403,
                )

        return wrapper

    return decorator


def feature_required(feature_name: str) -> Callable:
    """
    Decorator to gate functionality behind license features.

    Args:
        feature_name: Name of the required feature

    Returns:
        Decorated function

    Raises:
        FeatureNotAvailableError: If feature is not available
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = get_client()

            if client is None:
                logger.warning(
                    f"Feature '{feature_name}' required for {func.__name__} "
                    f"but license client not initialized"
                )
                return (
                    jsonify(
                        {
                            "error": "License not configured",
                            "message": f"Feature '{feature_name}' requires license",
                        }
                    ),
                    403,
                )

            try:
                if not client.check_feature(feature_name):
                    raise FeatureNotAvailableError(feature_name)

                # Proceed to the actual endpoint
                return func(*args, **kwargs)

            except FeatureNotAvailableError as e:
                logger.warning(
                    f"Feature '{feature_name}' not available for {func.__name__}: {e}"
                )
                return (
                    jsonify(
                        {
                            "error": "Feature not available",
                            "message": f"Feature '{feature_name}' requires license upgrade",
                        }
                    ),
                    403,
                )

        return wrapper

    return decorator


__all__ = [
    "license_required",
    "feature_required",
]
