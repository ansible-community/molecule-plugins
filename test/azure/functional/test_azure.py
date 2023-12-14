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

import pytest

from conftest import change_dir_to
from molecule import logger
from molecule.util import run_command

LOG = logger.get_logger(__name__)


def test_azure_command_init_scenario(temp_dir):
    role_directory = os.path.join(temp_dir.strpath, "test_init")
    cmd = ["ansible-galaxy", "role", "init", "test_init"]
    result = run_command(cmd)
    assert result.returncode == 0

    with change_dir_to(role_directory):
        # we need to inject namespace info into meta/main.yml
        cmd_meta = [
            "ansible",
            "localhost",
            "-o",  # one line output
            "-m",
            "lineinfile",
            "-a",
            'path=meta/main.yml line="  namespace: foo" insertafter="  author: your name"',
        ]
        run_command(cmd_meta, check=True)

        # we need to inject namespace info into tests/test.yml
        cmd_tests = [
            "ansible",
            "localhost",
            "-o",  # one line output
            "-m",
            "lineinfile",
            "-a",
            'path=tests/test.yml line="    - foo.test_init" regex="^(.*)  - test_init"',
        ]
        run_command(cmd_tests, check=True)

        molecule_directory = pytest.helpers.molecule_directory()
        scenario_directory = os.path.join(molecule_directory, "test_scenario")
        cmd = [
            "molecule",
            "init",
            "scenario",
            "test_scenario",
            "--driver-name",
            "azure",
        ]
        result = run_command(cmd)
        assert result.returncode == 0

        assert os.path.isdir(scenario_directory)

        # temporary trick to pass on CI/CD
        if "AZURE_SECRET" in os.environ:
            cmd = ["molecule", "test", "-s", "test-scenario"]
            result = run_command(cmd)
            assert result.returncode == 0
