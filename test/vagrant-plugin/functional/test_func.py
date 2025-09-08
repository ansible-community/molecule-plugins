#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#  Copyright (c) 2018 Red Hat, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import os
import platform
import shutil
from pathlib import Path

import pytest
import vagrant

from conftest import change_dir_to
from molecule import logger, util
from molecule.app import get_app

LOG = logger.get_logger(__name__)


def is_vagrant_supported() -> bool:
    """Return True if vagrant is installed and current platform is supported."""
    if not shutil.which("vagrant"):
        return False
    if not (platform.machine() == "arm64" and platform.system() == "Darwin"):
        return True


@pytest.mark.skipif(
    not is_vagrant_supported(),
    reason="vagrant not supported on this machine",
)
def test_vagrant_command_init_scenario(temp_dir):
    with change_dir_to(temp_dir):
        os.makedirs(os.path.join(temp_dir, "molecule", "default"))
        scenario_directory = os.path.join(temp_dir, "molecule", "test-scenario")
        cmd = [
            "molecule",
            "init",
            "scenario",
            "test-scenario",
            "--driver-name",
            "vagrant",
        ]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 0

        assert os.path.isdir(scenario_directory)

        # Clean unwanted default create/destroy files from molecule init
        os.unlink(os.path.join(scenario_directory, "create.yml"))
        os.unlink(os.path.join(scenario_directory, "destroy.yml"))

        confpath = os.path.join(scenario_directory, "molecule.yml")
        conf = util.safe_load_file(confpath)
        env = os.environ
        if "TESTBOX" in env:
            conf["platforms"][0]["box"] = env["TESTBOX"]
        if "vagrant-libvirt" in [x.name for x in vagrant.Vagrant().plugin_list()]:
            conf["driver"]["provider"] = {"name": "libvirt"}
        util.write_file(confpath, util.safe_dump(conf))
        cmd = ["molecule", "--debug", "test", "-s", "test-scenario"]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skipif(
    not is_vagrant_supported(),
    reason="vagrant not supported on this machine",
)
def test_invalid_settings(temp_dir):
    scenario_directory = os.path.join(
        os.path.dirname(util.abs_path(__file__)),
        os.path.pardir,
        "scenarios",
    )

    with change_dir_to(scenario_directory):
        cmd = ["molecule", "create", "--scenario-name", "invalid"]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 2

        assert "Failed to validate generated Vagrantfile" in result.stdout


@pytest.mark.skipif(
    not is_vagrant_supported(),
    reason="vagrant not supported on this machine",
)
@pytest.mark.parametrize(
    "scenario",
    [
        ("vagrant_root"),
        ("config_options"),
        ("provider_config_options"),
        ("default"),
        ("default-compat"),
        ("box_url"),
        ("network"),
        ("hostname"),
    ],
)
def test_vagrant_root(temp_dir, scenario):
    scenario_directory = os.path.join(
        os.path.dirname(util.abs_path(__file__)),
        os.path.pardir,
        "scenarios",
    )

    with change_dir_to(scenario_directory):
        cmd = ["molecule", "test", "--scenario-name", scenario]
        result = get_app(Path()).run_command(cmd)
        assert result.returncode == 0


@pytest.mark.skipif(
    not is_vagrant_supported(),
    reason="vagrant not supported on this machine",
)
def test_multi_node(temp_dir):
    scenario_directory = os.path.join(
        os.path.dirname(util.abs_path(__file__)),
        os.path.pardir,
        "scenarios",
    )

    molecule_eph_directory = os.path.join(temp_dir, "ephemeral")
    env = os.environ
    env["MOLECULE_EPHEMERAL_DIRECTORY"] = molecule_eph_directory

    with change_dir_to(scenario_directory):
        cmd = ["molecule", "test", "--scenario-name", "multi-node"]
        result = get_app(Path()).run_command(cmd, env=env)
        assert result.returncode == 0

    vagrantfile = os.path.join(
        molecule_eph_directory,
        "Vagrantfile",
    )
    with open(vagrantfile) as f:
        content = f.read()
        assert "instance-1" in content
        assert "instance-2" in content
