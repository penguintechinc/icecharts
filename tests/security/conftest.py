"""Security test fixtures."""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "services",
        "flask-backend",
    ),
)
from tests.conftest import *  # noqa: F401,F403
