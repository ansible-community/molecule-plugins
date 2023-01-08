"""Pytest Fixtures."""
import os
import platform

import pytest


def pytest_collection_finish(session):
    """Fail fast if current environment is broken."""
    if "CONTAINER_HOST" in os.environ and platform.system() != "Darwin":
        pytest.exit(
            msg="CONTAINER_HOST is defined, see https://github.com/containers/podman/issues/8070"
        )


@pytest.fixture
def driver_name() -> str:
    """Return name of the driver to be tested."""
    return "podman"
