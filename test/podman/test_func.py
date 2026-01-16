"""Functional tests."""

import os
import subprocess
from pathlib import Path

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


def test_sample() -> None:
    """Runs the sample scenario present at the repository root."""
    result = get_app(Path()).run_command(
        [
            "molecule",
            "test",
            "-s",
            "test-podman",
        ]
    )  # default scenario
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
