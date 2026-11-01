# Copyright (c) 2015-2018 Cisco Systems, Inc.
# Copyright (c) 2018 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Functional tests."""

from __future__ import annotations

import os
import pathlib
import subprocess

from pathlib import Path
from shutil import which

import pytest

from molecule.app import get_app

from conftest import change_dir_to, set_driver_in_scenario_molecule_yml
from molecule import logger
from molecule_plugins.podman import __file__ as module_file


LOG = logger.get_logger(__name__)


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return f"RC: {result.returncode}\n" + f"STDOUT: {result.stdout}\n" + f"STDERR: {result.stderr}"


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
        ]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0
        set_driver_in_scenario_molecule_yml(str(scenario_directory), "podman")

        assert scenario_directory.exists()

        # run molecule reset as this may clean some leftovers from other
        # test runs and also ensure that reset works.
        result = get_app(tmp_path).run_command(
            [
                "molecule",
                "reset",
            ]
        )  # default scenario
        assert result.returncode == 0

        result = get_app(tmp_path).run_command(
            [
                "molecule",
                "reset",
                "-s",
                scenario_name,
            ]
        )
        assert result.returncode == 0

        cmd = ["molecule", "--debug", "test", "-s", scenario_name]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skipif(
    not which("podman"),
    reason="""This scenario uses containers plugin and assumes that podman is installed
            But podman executable could not be found in PATH
            skipping test, as on this system it will fail anyway
            if you want this test to be run, then you would have to change the file src/molecule_plugins/podman/playbooks/create.yml:64
            """,
)
def test_sample() -> None:
    """Runs the sample scenario present at the repository root."""
    scenario_yml = Path("molecule/test-podman/molecule.yml")
    if not scenario_yml.exists():
        pytest.skip(
            "molecule/test-podman scenario not found (e.g. not at repo root or path changed)"
        )
    result = get_app(Path()).run_command(
        [
            "molecule",
            "test",
            "-s",
            "test-podman",
        ]
    )  # default scenario
    assert result.returncode == 0


def _is_transient_playbook_error(result: subprocess.CompletedProcess) -> bool:
    """True if output suggests a transient error (e.g. registry 504)."""
    out = (result.stdout or "") + (result.stderr or "")
    return "504" in out or "Gateway Time-out" in out or "Temporary failure" in out


@pytest.mark.skipif(
    not which("podman"),
    reason="""This scenario uses containers plugin and assumes that podman is installed
            But podman executable could not be found in PATH
            skipping test, as on this system it will fail anyway
            if you want this test to be run, then you would have to change the file src/molecule_plugins/podman/playbooks/create.yml:64
            """,
)
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
    max_attempts = 3
    for attempt in range(max_attempts):
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i",
                "localhost,",
                "playbooks/validate-dockerfile.yml",
            ],
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            shell=False,
            cwd=module_path,
            text=True,
            env=env,
        )
        if result.returncode == 0:
            return
        if attempt < max_attempts - 1 and _is_transient_playbook_error(result):
            continue
        break
    assert result.returncode == 0, format_result(result)
