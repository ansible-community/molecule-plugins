"""Functional tests."""

import os
import pathlib
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import change_dir_to, set_driver_in_scenario_molecule_yml
from molecule import logger
from molecule.app import get_app

LOG = logger.get_logger(__name__)

# Root of the test/docker tree (for scenario paths)
TEST_DOCKER_DIR = pathlib.Path(__file__).resolve().parent


def is_docker_available() -> bool:
    """Return True if Docker daemon is reachable (e.g. docker info succeeds)."""
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return (
        f"RC: {result.returncode}\n"
        + f"STDOUT: {result.stdout}\n"
        + f"STDERR: {result.stderr}"
    )


@pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available or daemon not reachable",
)
def test_command_init_and_test_scenario(tmp_path: pathlib.Path, DRIVER: str) -> None:
    """Verify that init scenario works."""
    shutil.rmtree(tmp_path, ignore_errors=True)
    tmp_path.mkdir(exist_ok=True)

    scenario_name = "default"

    with change_dir_to(tmp_path):
        scenario_directory = tmp_path / "molecule" / scenario_name
        cmd = [
            "molecule",
            "init",
            "scenario",
            scenario_name,
        ]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0
        set_driver_in_scenario_molecule_yml(str(scenario_directory), DRIVER)

        assert scenario_directory.exists()

        # run molecule reset as this may clean some leftovers from other
        # test runs and also ensure that reset works.
        result = get_app(tmp_path).run_command(
            ["molecule", "reset"]
        )  # default scenario
        assert result.returncode == 0

        result = get_app(tmp_path).run_command(
            ["molecule", "reset", "-s", scenario_name]
        )
        assert result.returncode == 0

        cmd = ["molecule", "--debug", "test", "-s", scenario_name]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available or daemon not reachable",
)
def test_command_static_scenario() -> None:
    """Validate that the scenario we included with code still works."""
    scenario_dir = TEST_DOCKER_DIR / "scenarios" / "with-context"
    with change_dir_to(str(scenario_dir)):
        result = get_app(Path()).run_command(["molecule", "test"])
        assert result.returncode == 0


@pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available or daemon not reachable",
)
def test_dockerfile_with_context() -> None:
    """Verify that Dockerfile.j2 with context works."""
    scenario_dir = TEST_DOCKER_DIR / "scenarios" / "with-context"
    with change_dir_to(str(scenario_dir)):
        result = get_app(Path()).run_command(["molecule", "--debug", "test"])
        assert result.returncode == 0


@pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available or daemon not reachable",
)
def test_env_substitution() -> None:
    """Verify that env variables in molecule.yml are replaced properly."""
    os.environ["MOLECULE_ROLE_IMAGE"] = "debian:bullseye"
    try:
        scenario_dir = TEST_DOCKER_DIR / "scenarios" / "env-substitution"
        with change_dir_to(str(scenario_dir)):
            result = get_app(Path()).run_command(["molecule", "--debug", "test"])
            assert result.returncode == 0
    finally:
        os.environ.pop("MOLECULE_ROLE_IMAGE", None)
