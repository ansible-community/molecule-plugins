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
from pathlib import Path

import pytest

from conftest import (
    change_dir_to,
    set_driver_in_scenario_molecule_yml,
)
from molecule import logger
from molecule.app import get_app

LOG = logger.get_logger(__name__)
driver_name = __name__.split(".")[0].split("_")[-1]


def test_gce_command_init_scenario(temp_dir):
    """Test init scenario with driver; run molecule test only with GCE creds."""
    role_directory = os.path.join(temp_dir.strpath, "test-init")
    # molecule init role was removed in molecule 25.x; use ansible-galaxy like Azure test
    cmd = ["ansible-galaxy", "role", "init", "test-init"]
    assert get_app(Path()).run_command(cmd).returncode == 0

    with change_dir_to(role_directory):
        molecule_directory = pytest.helpers.molecule_directory()
        scenario_directory = os.path.join(molecule_directory, "test-scenario")
        cmd = ["molecule", "init", "scenario", "test-scenario"]
        assert get_app(Path()).run_command(cmd).returncode == 0
        set_driver_in_scenario_molecule_yml(scenario_directory, driver_name)

        assert os.path.isdir(scenario_directory)
        has_creds = "GOOGLE_APPLICATION_CREDENTIALS" in os.environ
        if not has_creds:
            os.unlink(os.path.join(scenario_directory, "create.yml"))
            os.unlink(os.path.join(scenario_directory, "destroy.yml"))

        # Run full molecule test only when GCE credentials are available
        if has_creds:
            cmd = ["molecule", "test", "-s", "test-scenario"]
            assert get_app(Path()).run_command(cmd).returncode == 0
