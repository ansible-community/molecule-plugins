"""Driver playbook tests, run against a limactl stub."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from molecule import api, util

PLATFORMS = [
    {"name": "minimal"},
    {
        "name": "full",
        "lima_template": "ubuntu-24.04",
        "cpus": 2,
        "memory": 2,
        "disk": 20,
        "arch": "aarch64",
        "vm_type": "vz",
    },
    {"name": "locator", "lima_template": "https://example.com/lima.yaml"},
]


@pytest.fixture()
def lima_env(limactl_stub: Path, tmp_path: Path):
    """Return an environment where limactl is replaced by the stub."""
    env = dict(os.environ)
    env["PATH"] = f"{limactl_stub}{os.pathsep}{env['PATH']}"
    env["LIMACTL_STATE_DIR"] = str(tmp_path)
    env.pop("ANSIBLE_INVENTORY", None)
    return env


def run_playbook(step: str, env: dict[str, str], tmp_path: Path, platforms: list[dict]):
    """Run a driver playbook and return the instance config it wrote."""
    playbook = api.drivers()["lima"].get_playbook(step)
    assert playbook is not None

    instance_config = tmp_path / "instance_config.yml"
    extra_vars = {
        "molecule_no_log": False,
        "molecule_instance_config": str(instance_config),
        "molecule_yml": {"platforms": platforms},
    }
    result = subprocess.run(
        [
            "ansible-playbook",
            "-i",
            "localhost,",
            "-e",
            json.dumps(extra_vars),
            playbook,
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return util.safe_load_file(str(instance_config))


def limactl_calls(tmp_path: Path, command: str) -> list[list[str]]:
    """Return the stub invocations starting with the given command."""
    lines = (tmp_path / "calls.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines if json.loads(line)[:1] == [command]]


def instance_name(call: list[str]) -> str:
    """Return the instance name passed to a limactl start call."""
    return next(a.removeprefix("--name=") for a in call if a.startswith("--name="))


def test_create_starts_every_platform(lima_env, tmp_path):
    """Asserts that create starts one instance per platform."""
    instance_config = run_playbook("create", lima_env, tmp_path, PLATFORMS)

    assert [c[-1] for c in limactl_calls(tmp_path, "start")] == [
        "template:debian-12",
        "template:ubuntu-24.04",
        "https://example.com/lima.yaml",
    ]
    assert {entry["instance"] for entry in instance_config} == {
        "minimal",
        "full",
        "locator",
    }
    assert instance_config[0]["user"] == "tester"
    assert instance_config[0]["address"] == "127.0.0.1"
    assert instance_config[0]["identity_file"].endswith("minimal")
    assert isinstance(instance_config[0]["port"], int)


def test_create_passes_platform_options(lima_env, tmp_path):
    """Asserts that platform options are forwarded to limactl."""
    run_playbook("create", lima_env, tmp_path, PLATFORMS)

    started = {instance_name(c): c for c in limactl_calls(tmp_path, "start")}
    assert started["full"] == [
        "start",
        "--plain",
        "--tty=false",
        "--name=full",
        "--cpus=2",
        "--memory=2",
        "--disk=20",
        "--arch=aarch64",
        "--vm-type=vz",
        "template:ubuntu-24.04",
    ]
    assert started["minimal"] == [
        "start",
        "--plain",
        "--tty=false",
        "--name=minimal",
        "template:debian-12",
    ]


def test_create_skips_existing_instances(lima_env, tmp_path):
    """Asserts that create does not restart an instance that already exists."""
    (tmp_path / "instances.json").write_text(json.dumps(["minimal"]))

    instance_config = run_playbook("create", lima_env, tmp_path, PLATFORMS)

    assert [instance_name(c) for c in limactl_calls(tmp_path, "start")] == [
        "full",
        "locator",
    ]
    assert len(instance_config) == len(PLATFORMS)


def test_destroy_deletes_every_platform(lima_env, tmp_path):
    """Asserts that destroy removes the instances and empties the config."""
    (tmp_path / "instances.json").write_text(
        json.dumps([platform["name"] for platform in PLATFORMS]),
    )

    instance_config = run_playbook("destroy", lima_env, tmp_path, PLATFORMS)

    assert limactl_calls(tmp_path, "delete") == [
        ["delete", "--force", "minimal"],
        ["delete", "--force", "full"],
        ["delete", "--force", "locator"],
    ]
    assert json.loads((tmp_path / "instances.json").read_text()) == []
    assert not instance_config


def test_destroy_skips_instances_that_are_gone(lima_env, tmp_path):
    """Asserts that destroy only deletes instances that still exist."""
    (tmp_path / "instances.json").write_text(json.dumps(["full"]))

    run_playbook("destroy", lima_env, tmp_path, PLATFORMS)

    assert limactl_calls(tmp_path, "delete") == [["delete", "--force", "full"]]
