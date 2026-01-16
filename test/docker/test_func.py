"""Functional tests."""

import os
import subprocess
from pathlib import Path

import pytest

from conftest import change_dir_to
from molecule import logger
from molecule.app import get_app

LOG = logger.get_logger(__name__)


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return (
        f"RC: {result.returncode}\n"
        + f"STDOUT: {result.stdout}\n"
        + f"STDERR: {result.stderr}"
    )


@pytest.mark.skip(reason="broken, fix welcomed")
def test_command_static_scenario() -> None:
    """Validate that the scenario we included with code still works."""
    cmd = ["molecule", "test"]

    result = get_app(Path()).run_command(cmd)
    assert result.returncode == 0


@pytest.mark.skip(reason="broken, fix welcomed")
def test_dockerfile_with_context() -> None:
    """Verify that Dockerfile.j2 with context works."""
    with change_dir_to("test/docker/scenarios/with-context"):
        cmd = ["molecule", "--debug", "test"]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skip(reason="broken, fix welcomed")
def test_env_substitution() -> None:
    """Verify that env variables in molecule.yml are replaced properly."""
    os.environ["MOLECULE_ROLE_IMAGE"] = "debian:bullseye"
    with change_dir_to("test/docker/scenarios/env-substitution"):
        cmd = ["molecule", "--debug", "test"]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 0
