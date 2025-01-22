"""Functional tests."""

import os
import pathlib
import subprocess
from pathlib import Path

from conftest import change_dir_to
from molecule import logger
from molecule.app import get_app
from molecule_plugins.podman import __file__ as module_file

LOG = logger.get_logger(__name__)


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return (
        f"RC: {result.returncode}\n"
        + f"STDOUT: {result.stdout}\n"
        + f"STDERR: {result.stderr}"
    )


def test_podman_command_init_scenario(tmp_path: pathlib.Path):
    """Verify that init scenario works."""
    scenario_name = "default"

    with change_dir_to(tmp_path):
        scenario_directory = tmp_path / "molecule" / scenario_name
        cmd = [
            "molecule",
            "init",
            "scenario",
            scenario_name,
            "--driver-name",
            "podman",
        ]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0

        assert scenario_directory.exists()

        # run molecule reset as this may clean some leftovers from other
        # test runs and also ensure that reset works.
        result = get_app(tmp_path).run_command(
            ["molecule", "reset"]
        )  # default sceanario
        assert result.returncode == 0

        result = get_app(tmp_path).run_command(
            ["molecule", "reset", "-s", scenario_name]
        )
        assert result.returncode == 0

        cmd = ["molecule", "--debug", "test", "-s", scenario_name]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0


def test_sample() -> None:
    """Runs the sample scenario present at the repository root."""
    result = get_app(Path()).run_command(
        ["molecule", "test", "-s", "test-podman"]
    )  # default sceanario
    assert result.returncode == 0


def test_dockerfile():
    """Verify that our embedded dockerfile can be build."""
    result = subprocess.run(
        ["ansible-playbook", "--version"],
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        shell=False,
        text=True,
    )
    assert result.returncode == 0, result
    assert "ansible-playbook" in result.stdout

    module_path = os.path.dirname(module_file)
    assert os.path.isdir(module_path)
    env = os.environ.copy()
    env["ANSIBLE_FORCE_COLOR"] = "0"
    result = subprocess.run(
        ["ansible-playbook", "-i", "localhost,", "playbooks/validate-dockerfile.yml"],
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        shell=False,
        cwd=module_path,
        text=True,
        env=env,
    )
    assert result.returncode == 0, format_result(result)
    # , result
