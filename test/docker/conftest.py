"""Pytest Fixtures."""

from conftest import random_string, temp_dir  # noqa

import pytest


@pytest.fixture()
def driver_name():
    """Return name of the driver to be tested."""
    return "docker"
