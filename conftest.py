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

from __future__ import annotations

import contextlib
import os
import random
import re
import shutil
import string

from pathlib import Path

import pytest

from molecule.app import get_app

from molecule import config, logger


LOG = logger.get_logger(__name__)


@pytest.helpers.register
def run_command(cmd, env=os.environ, log=True):
    if cmd.__class__.__name__ == "Command":
        if log:
            cmd = _rebake_command(cmd, env)
        cmd = cmd.bake(_truncate_exc=False)
    return get_app(Path()).run_command(cmd, env=env)


def _rebake_command(cmd, env, out=LOG.info, err=LOG.error):
    return cmd.bake(_env=env, _out=out, _err=err)


@pytest.fixture()
def random_string(length=5):
    return "".join(random.choice(string.ascii_uppercase) for _ in range(length))


@contextlib.contextmanager
def change_dir_to(dir_name):
    cwd = os.getcwd()
    os.chdir(dir_name)
    yield
    os.chdir(cwd)


@pytest.fixture()
def temp_dir(tmpdir, random_string, request):
    directory = tmpdir.mkdir(random_string)

    with change_dir_to(directory.strpath):
        yield directory


@pytest.fixture()
def resources_folder_path():
    resources_folder_path = os.path.join(os.path.dirname(__file__), "resources")
    return resources_folder_path


@pytest.helpers.register
def molecule_project_directory():
    return os.getcwd()


@pytest.helpers.register
def molecule_directory():
    return config.molecule_directory(molecule_project_directory())


@pytest.helpers.register
def molecule_scenario_directory():
    return os.path.join(molecule_directory(), "default")


@pytest.helpers.register
def molecule_file():
    return get_molecule_file(molecule_scenario_directory())


@pytest.helpers.register
def get_molecule_file(path):
    return config.molecule_file(path)


def set_driver_in_scenario_molecule_yml(scenario_directory: str, driver_name: str) -> None:
    """Set driver name in molecule.yml after 'molecule init scenario' (no --driver-name).

    Molecule 4.x+ removed --driver-name from 'init scenario'. Init then patch the file.
    """
    molecule_yml = os.path.join(scenario_directory, "molecule.yml")
    with open(molecule_yml) as f:
        content = f.read()
    driver_block = f"\ndriver:\n  name: {driver_name}\n"
    if "driver:" not in content:
        content = content.replace("---\n", "---" + driver_block, 1)
    else:
        content = re.sub(
            r"(driver:\s*\n\s*name:)\s*\w+",
            f"\\1 {driver_name}",
            content,
            count=1,
        )
    with open(molecule_yml, "w") as f:
        f.write(content)


def metadata_lint_update(role_directory: str) -> None:
    # By default, ansible-lint will fail on newly-created roles because the
    # fields in this file have not been changed from their defaults. This is
    # good because molecule should create this file using the defaults, and
    # users should receive feedback to change these defaults. However, this
    # blocks the testing of 'molecule init' itself, so ansible-lint should
    # be configured to ignore these metadata lint errors.
    dirname = os.path.dirname(os.path.abspath(__file__))
    ansible_lint_src = os.path.join(dirname, ".config", "ansible-lint.yaml")
    config_dir = os.path.join(role_directory, ".config")
    os.makedirs(config_dir, exist_ok=True)
    shutil.copy(ansible_lint_src, config_dir)

    # Explicitly lint here to catch any unexpected lint errors before
    # continuing functional testing. Ansible lint is run at the root
    # of the role directory and pointed at the role directory to ensure
    # the customize ansible-lint config is used.
    with change_dir_to(role_directory):
        cmd = ["ansible-lint", "."]
        result = run_command(cmd)
    assert result.returncode == 0
