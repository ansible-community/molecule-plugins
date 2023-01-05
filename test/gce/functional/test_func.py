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

import pytest
import os

from molecule import logger
from molecule.util import run_command
from molecule.test.conftest import change_dir_to
from molecule.test.functional.conftest import metadata_lint_update

LOG = logger.get_logger(__name__)
driver_name = __name__.split(".")[0].split("_")[-1]


@pytest.mark.xfail(reason="need to fix template path")
def test_command_init_scenario(temp_dir):
    """Test init scenario with driver."""
    role_directory = os.path.join(temp_dir.strpath, "test-init")
    cmd = ["molecule", "init", "role", "test-init"]
    assert run_command(cmd).returncode == 0
    metadata_lint_update(role_directory)

    with change_dir_to(role_directory):
        molecule_directory = pytest.helpers.molecule_directory()
        scenario_directory = os.path.join(molecule_directory, "test-scenario")
        cmd = [
            "molecule",
            "init",
            "scenario",
            "test-scenario",
            "--role-name",
            "test-init",
            "--driver-name",
            driver_name,
        ]
        assert run_command(cmd).returncode == 0

        assert os.path.isdir(scenario_directory)

        cmd = ["molecule", "test", "-s", "test-scenario"]
        assert run_command(cmd).returncode == 0
