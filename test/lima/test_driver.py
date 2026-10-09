# Copyright (c) 2026 Josef Simanek

"""Unit tests."""

from __future__ import annotations

import json
import os

from pathlib import Path

import pytest

from jsonschema import Draft202012Validator, ValidationError, validate
from molecule.exceptions import MoleculeError

from molecule import api
from molecule_plugins.lima.driver import Lima


class _FakeConfig:
    """Minimal stand-in for a molecule config object."""

    def __init__(self) -> None:
        data = {"driver": {"ssh_connection_options": []}}
        # molecule renamed Config.config to Config.config_data
        self.config = data
        self.config_data = data


def test_lima_driver_is_detected(driver_name: str):
    """Asserts that molecule recognizes the driver.

    Args:
        driver_name: Driver name under test.
    """
    assert driver_name in [str(d) for d in api.drivers()]


def test_lima_driver_provides_schema(driver_name: str):
    """Asserts that the lima driver provides a JSON schema file.

    Args:
        driver_name: Driver name under test.
    """
    driver = api.drivers()[driver_name]
    schema_file = driver.schema_file()

    assert schema_file is not None
    assert Path(schema_file).is_file()
    assert schema_file.endswith(driver_name + "/schema/driver.json")


def test_lima_driver_schema_is_valid(driver_name: str):
    """Asserts that the lima driver schema is a valid JSON Schema.

    Args:
        driver_name: Driver name under test.
    """
    schema_file = api.drivers()[driver_name].schema_file()
    schema = json.loads(Path(schema_file).read_text())
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    ("config", "valid"),
    [
        # Minimal valid configuration
        (
            {
                "driver": {"name": "lima"},
                "platforms": [{"name": "instance"}],
            },
            True,
        ),
        # Comprehensive configuration exercising all documented options
        (
            {
                "driver": {"name": "lima"},
                "platforms": [
                    {
                        "arch": "x86_64",
                        "cpus": 2,
                        "disk": 50,
                        "groups": ["webserver"],
                        "lima_template": "debian-12",
                        "memory": 4,
                        "name": "instance",
                        "vm_type": "qemu",
                    },
                ],
            },
            True,
        ),
        # Unknown platform options must be rejected
        (
            {
                "driver": {"name": "lima"},
                "platforms": [{"name": "instance", "image": "image:tag"}],
            },
            False,
        ),
        # Platform name is required
        (
            {
                "driver": {"name": "lima"},
                "platforms": [{"lima_template": "debian-12"}],
            },
            False,
        ),
    ],
)
def test_lima_driver_schema_validation(config: dict, valid: bool):
    """Asserts that the lima driver schema accepts/rejects configs correctly.

    Args:
        config: Molecule configuration.
        valid: Whether the configuration should pass validation.
    """
    schema_file = api.drivers()["lima"].schema_file()
    schema = json.loads(Path(schema_file).read_text())
    if valid:
        validate(instance=config, schema=schema)
    else:
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)


def test_driver_initializes_without_limactl_executable(monkeypatch: pytest.MonkeyPatch):
    """Make sure we can initialize driver without having an executable present.

    Args:
        monkeypatch: Fixture for replacing runtime values.
    """
    monkeypatch.setenv("PATH", "")
    Lima()


def test_driver_sanity_check_fails_without_limactl_executable(monkeypatch: pytest.MonkeyPatch):
    """Make sure sanity checks report a missing executable.

    Args:
        monkeypatch: Fixture for replacing runtime values.
    """
    monkeypatch.setenv("PATH", "")
    with pytest.raises((MoleculeError, SystemExit)):
        Lima().sanity_checks()


def test_driver_sanity_check_accepts_supported_lima(
    monkeypatch: pytest.MonkeyPatch, limactl_stub: Path, tmp_path: Path
):
    """Make sure sanity checks pass with a supported Lima version.

    Args:
        monkeypatch: Fixture for replacing runtime values.
        limactl_stub: Directory containing the Lima command stub.
        tmp_path: Temporary directory for the test.
    """
    monkeypatch.setenv("PATH", f"{limactl_stub}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LIMACTL_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("LIMACTL_VERSION", "2.0.0")

    Lima().sanity_checks()


def test_driver_sanity_check_rejects_old_lima(
    monkeypatch: pytest.MonkeyPatch, limactl_stub: Path, tmp_path: Path
):
    """Make sure sanity checks reject a Lima release older than 2.0.

    Args:
        monkeypatch: Fixture for replacing runtime values.
        limactl_stub: Directory containing the Lima command stub.
        tmp_path: Temporary directory for the test.
    """
    monkeypatch.setenv("PATH", f"{limactl_stub}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LIMACTL_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("LIMACTL_VERSION", "1.2.2")

    with pytest.raises((MoleculeError, SystemExit)):
        Lima().sanity_checks()


def test_login_command_targets_the_instance():
    """Asserts that the login command is rendered for a given instance."""
    driver = Lima()
    command = driver.login_cmd_template.format(**driver.login_options("instance"))

    assert command == "limactl shell instance"


def test_ansible_connection_options_map_instance_config(monkeypatch: pytest.MonkeyPatch):
    """Asserts that the instance config is mapped to connection options.

    Args:
        monkeypatch: Fixture for replacing runtime values.
    """
    driver = Lima(_FakeConfig())
    monkeypatch.setattr(
        driver,
        "_get_instance_config",
        lambda instance_name: {
            "user": "tester",
            "address": "127.0.0.1",
            "port": 60001,
            "identity_file": "/home/tester/.lima/_config/user",
        },
    )

    options = driver.ansible_connection_options("instance")

    assert options["ansible_user"] == "tester"
    assert options["ansible_host"] == "127.0.0.1"
    assert options["ansible_port"] == 60001
    assert options["ansible_private_key_file"] == "/home/tester/.lima/_config/user"
    assert options["ansible_connection"] == "ssh"
    assert "-o StrictHostKeyChecking=no" in options["ansible_ssh_common_args"]


def test_ansible_connection_options_without_instance_config(monkeypatch: pytest.MonkeyPatch):
    """Asserts that connection options are empty before instances exist.

    Args:
        monkeypatch: Fixture for replacing runtime values.
    """
    driver = Lima(_FakeConfig())

    def raise_os_error(instance_name):
        raise OSError

    monkeypatch.setattr(driver, "_get_instance_config", raise_os_error)

    assert driver.ansible_connection_options("instance") == {}
