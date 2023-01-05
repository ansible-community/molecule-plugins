"""Functional tests."""
import os
import pathlib
import shutil
import subprocess
import pytest

from molecule import logger
from molecule.test.conftest import change_dir_to
from molecule.util import run_command

LOG = logger.get_logger(__name__)


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return (
        f"RC: {result.returncode}\n"
        + f"STDOUT: {result.stdout}\n"
        + f"STDERR: {result.stderr}"
    )


@pytest.mark.skip(reason="broken, fix welcomed")
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
            "--driver-name",
            DRIVER,
        ]
        result = run_command(cmd)
        assert result.returncode == 0

        assert scenario_directory.exists()

        # run molecule reset as this may clean some leftovers from other
        # test runs and also ensure that reset works.
        result = run_command(["molecule", "reset"])  # default scenario
        assert result.returncode == 0

        result = run_command(["molecule", "reset", "-s", scenario_name])
        assert result.returncode == 0

        cmd = ["molecule", "--debug", "test", "-s", scenario_name]
        result = run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skip(reason="broken, fix welcomed")
def test_command_static_scenario() -> None:
    """Validate that the scenario we included with code still works."""
    cmd = ["molecule", "test"]

    result = run_command(cmd)
    assert result.returncode == 0


@pytest.mark.skip(reason="broken, fix welcomed")
def test_dockerfile_with_context() -> None:
    """Verify that Dockerfile.j2 with context works."""
    with change_dir_to("test/docker/scenarios/with-context"):
        cmd = ["molecule", "--debug", "test"]
        result = run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skip(reason="broken, fix welcomed")
def test_env_substitution() -> None:
    """Verify that env variables in molecule.yml are replaced properly."""
    os.environ["MOLECULE_ROLE_IMAGE"] = "debian:bullseye"
    with change_dir_to("test/docker/scenarios/env-substitution"):
        cmd = ["molecule", "--debug", "test"]
        result = run_command(cmd)
        assert result.returncode == 0
