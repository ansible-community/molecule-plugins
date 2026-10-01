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

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import subprocess

import os
import pathlib
import shutil

from pathlib import Path

import pytest

from molecule.app import get_app

import openstack

from conftest import change_dir_to, set_driver_in_scenario_molecule_yml
from molecule import logger


LOG = logger.get_logger(__name__)


def is_openstack_auth() -> bool:
    """Is the openstack authentication config in place?"""

    try:
        conn = openstack.connect()
        list(conn.compute.servers())
        return True
    except Exception:
        return False


def format_result(result: subprocess.CompletedProcess):
    """Return friendly representation of completed process run."""
    return f"RC: {result.returncode}\n" + f"STDOUT: {result.stdout}\n" + f"STDERR: {result.stderr}"


@pytest.mark.skipif(not is_openstack_auth(), reason="Openstack authentication missing")
def test_openstack_init_and_test_scenario(tmp_path: pathlib.Path, DRIVER: str) -> None:
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
        os.unlink(os.path.join(scenario_directory, "create.yml"))
        os.unlink(os.path.join(scenario_directory, "destroy.yml"))

        confpath = os.path.join(scenario_directory, "molecule.yml")
        testconf = os.path.join(
            os.path.dirname(__file__),
            "scenarios/molecule",
            scenario_name,
            "molecule.yml",
        )

        shutil.copyfile(testconf, confpath)

        cmd = ["molecule", "--debug", "test", "-s", scenario_name]
        result = get_app(tmp_path).run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skipif(not is_openstack_auth(), reason="Openstack authentication missing")
@pytest.mark.parametrize(
    "scenario",
    [("multiple"), ("security_group"), ("network"), ("volume")],
)
def test_specific_scenarios(temp_dir, scenario) -> None:
    """Verify that specific scenarios work"""
    scenario_directory = os.path.join(os.path.dirname(__file__), "scenarios")

    with change_dir_to(scenario_directory):
        cmd = ["molecule", "test", "--scenario-name", scenario]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 0
