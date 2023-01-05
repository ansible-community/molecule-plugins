"""Pytest Fixtures."""
import pytest
from molecule.test.conftest import random_string, temp_dir  # noqa


@pytest.fixture
def DRIVER():
    """Return name of the driver to be tested."""
    return "docker"
