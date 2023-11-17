import contextlib
import os
import random
import shutil
import string

import pytest

from molecule import config, logger, util
from molecule.scenario import ephemeral_directory

LOG = logger.get_logger(__name__)


@pytest.helpers.register
def run_command(cmd, env=os.environ, log=True):
    if cmd.__class__.__name__ == "Command":
        if log:
            cmd = _rebake_command(cmd, env)
        cmd = cmd.bake(_truncate_exc=False)
    return util.run_command(cmd, env=env)


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


@pytest.helpers.register
def molecule_ephemeral_directory(_fixture_uuid):
    project_directory = f"test-project-{_fixture_uuid}"
    scenario_name = "test-instance"

    return ephemeral_directory(
        os.path.join("molecule_test", project_directory, scenario_name),
    )


def metadata_lint_update(role_directory: str) -> None:
    # By default, ansible-lint will fail on newly-created roles because the
    # fields in this file have not been changed from their defaults. This is
    # good because molecule should create this file using the defaults, and
    # users should receive feedback to change these defaults. However, this
    # blocks the testing of 'molecule init' itself, so ansible-lint should
    # be configured to ignore these metadata lint errors.
    dirname = os.path.dirname(os.path.abspath(__file__))
    ansible_lint_src = os.path.join(dirname, ".ansible-lint")
    shutil.copy(ansible_lint_src, role_directory)

    # Explicitly lint here to catch any unexpected lint errors before
    # continuining functional testing. Ansible lint is run at the root
    # of the role directory and pointed at the role directory to ensure
    # the customize ansible-lint config is used.
    with change_dir_to(role_directory):
        cmd = ["ansible-lint", "."]
        result = run_command(cmd)
    assert result.returncode == 0
