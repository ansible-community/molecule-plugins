"""Functional tests."""

import json
import pathlib
import shlex
import shutil
import subprocess
from importlib import resources

import pytest
from jsonschema import Draft202012Validator

from conftest import change_dir_to, set_driver_in_scenario_molecule_yml
from molecule import api, util
from molecule.app import get_app


def is_lima_available() -> bool:
    """Return True if limactl is installed."""
    return shutil.which("limactl") is not None


def molecule_accepts_lima_driver() -> bool:
    """Return True if molecule validates a scenario using the lima driver.

    Molecule checks molecule.yml against a bundled schema that enumerates the
    driver names it knows about, so scenarios cannot run before lima is part
    of that enumeration.
    """
    schema_file = resources.files("molecule") / "data" / "molecule.json"
    try:
        schema = json.loads(schema_file.read_text())
    except (OSError, ValueError):
        return True

    validator = Draft202012Validator(schema)
    config = {"driver": {"name": "lima"}, "platforms": [{"name": "instance"}]}

    return not [
        error
        for error in validator.iter_errors(config)
        if list(error.absolute_path)[:2] == ["driver", "name"]
    ]


needs_lima = pytest.mark.skipif(
    not is_lima_available(),
    reason="limactl not available",
)

needs_driver_name = pytest.mark.skipif(
    not molecule_accepts_lima_driver(),
    reason="molecule does not accept the lima driver name yet",
)


def prepare_scenario(tmp_path: pathlib.Path, platforms: list[dict]) -> str:
    """Initialize a scenario using the lima driver and return its name."""
    scenario_name = "default"
    scenario_directory = tmp_path / "molecule" / scenario_name

    result = get_app(tmp_path).run_command(
        ["molecule", "init", "scenario", scenario_name],
    )
    assert result.returncode == 0
    assert scenario_directory.exists()

    set_driver_in_scenario_molecule_yml(str(scenario_directory), "lima")

    # Molecule ships default create/destroy playbooks, the driver provides
    # its own.
    (scenario_directory / "create.yml").unlink()
    (scenario_directory / "destroy.yml").unlink()

    # The generated converge playbook refers to a placeholder role.
    (scenario_directory / "converge.yml").write_text(
        "---\n"
        "- name: Converge\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Check connection\n"
        "      ansible.builtin.ping:\n",
    )

    confpath = str(scenario_directory / "molecule.yml")
    conf = util.safe_load_file(confpath)
    conf["platforms"] = platforms
    util.write_file(confpath, util.safe_dump(conf))

    return scenario_name


@needs_lima
@needs_driver_name
def test_lima_command_init_and_test_scenario(tmp_path: pathlib.Path) -> None:
    """Verify that a multi node scenario using the lima driver can be tested."""
    platforms = [
        {
            "name": "instance-1",
            "lima_template": "debian-12",
            "cpus": 2,
            "memory": 2,
            "disk": 20,
        },
        {
            "name": "instance-2",
            "lima_template": "debian-12",
            "memory": 2,
            "disk": 20,
            "groups": ["extra"],
        },
    ]

    with change_dir_to(tmp_path):
        scenario_name = prepare_scenario(tmp_path, platforms)

        result = get_app(tmp_path).run_command(
            ["molecule", "test", "-s", scenario_name],
        )
        assert result.returncode == 0


@needs_lima
@needs_driver_name
def test_lima_login_command_reaches_the_instance(tmp_path: pathlib.Path) -> None:
    """Verify that the login command opens a shell on a created instance."""
    platforms = [
        {
            "name": "login-instance",
            "lima_template": "debian-12",
            "memory": 2,
            "disk": 20,
        },
    ]

    with change_dir_to(tmp_path):
        scenario_name = prepare_scenario(tmp_path, platforms)

        result = get_app(tmp_path).run_command(
            ["molecule", "create", "-s", scenario_name],
        )
        assert result.returncode == 0

        try:
            driver = api.drivers()["lima"]
            command = driver.login_cmd_template.format(
                **driver.login_options("login-instance"),
            )
            login = subprocess.run(
                [*shlex.split(command), "true"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert login.returncode == 0, login.stderr
        finally:
            result = get_app(tmp_path).run_command(
                ["molecule", "destroy", "-s", scenario_name],
            )
            assert result.returncode == 0
