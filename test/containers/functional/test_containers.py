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
"""Functional Tests."""
import os

from molecule import logger
from molecule.test.conftest import change_dir_to, molecule_directory
from molecule.util import run_command

LOG = logger.get_logger(__name__)


def test_command_init_scenario(temp_dir):
    """Verify that we can initialize a new scenario with this driver."""
    with change_dir_to(temp_dir):
        scenario_directory = os.path.join(molecule_directory(), "default")
        cmd = [
            "molecule",
            "init",
            "scenario",
            "default",
            "--driver-name",
            "containers",
        ]
        result = run_command(cmd)
        assert result.returncode == 0

        assert os.path.isdir(scenario_directory)

        # we do not run the full "test" sequence because lint will fail, check
        # is shorter but comprehensive enough to test the most important
        # functionality: destroy, dependency, create, prepare, converge
        cmd = ["molecule", "check", "-s", "default"]
        result = run_command(cmd)
        assert result.returncode == 0
