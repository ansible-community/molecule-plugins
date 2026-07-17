"""Unit tests."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError, validate

from molecule import api


def test_container_driver_is_detected(driver_name: str):
    """Asserts that molecule recognizes the driver."""
    assert driver_name in [str(d) for d in api.drivers()]


def test_container_driver_provides_schema(driver_name: str):
    """Asserts that the containers driver provides a JSON schema file."""
    driver = api.drivers()[driver_name]
    schema_file = driver.schema_file()

    assert schema_file is not None
    assert Path(schema_file).is_file()
    assert schema_file.endswith(driver_name + "/schema/driver.json")


def test_container_driver_schema_is_valid(driver_name: str):
    """Asserts that the containers driver schema is a valid JSON Schema."""
    schema_file = api.drivers()[driver_name].schema_file()
    schema = json.loads(Path(schema_file).read_text())
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    ("config", "valid"),
    [
        # Minimal valid configuration
        (
            {
                "driver": {"name": "containers"},
                "platforms": [{"name": "instance", "image": "image:tag"}],
            },
            True,
        ),
        # Comprehensive configuration exercising all documented options. Only
        # options that are portable across both the docker and podman backends
        # are accepted by the agnostic containers driver schema.
        (
            {
                "driver": {"name": "containers"},
                "platforms": [
                    {
                        "name": "instance",
                        "hostname": "instance",
                        "image": "image:tag",
                        "dockerfile": "Dockerfile.j2",
                        "pull": True,
                        "pre_build_image": False,
                        "registry": {
                            "url": "registry.example.com",
                            "credentials": {"username": "u", "password": "p"},
                        },
                        "override_command": True,
                        "command": "sleep infinity",
                        "tty": True,
                        "pid_mode": "host",
                        "privileged": True,
                        "security_opts": ["seccomp=unconfined"],
                        "devices": ["/dev/fuse:/dev/fuse:rwm"],
                        "volumes": ["/sys/fs/cgroup:/sys/fs/cgroup:ro"],
                        "tmpfs": ["/tmp", "/run"],
                        "capabilities": ["SYS_ADMIN"],
                        "exposed_ports": ["53/udp"],
                        "published_ports": ["0.0.0.0:8053:53/udp"],
                        "ulimits": ["nofile:262144:262144"],
                        "dns_servers": ["8.8.8.8"],
                        "etc_hosts": {"host1.example.com": "10.3.1.5"},
                        "env": {"FOO": "bar"},
                        "groups": ["webserver", "db"],
                        "cert_path": "/foo/bar/cert.pem",
                        "tls_verify": True,
                        "restart_policy": "on-failure",
                        "restart_retries": 1,
                        "buildargs": {"http_proxy": "http://proxy:8080/"},
                    }
                ],
            },
            True,
        ),
        # Docker-only option must be rejected
        (
            {
                "driver": {"name": "containers"},
                "platforms": [
                    {
                        "name": "instance",
                        "image": "image:tag",
                        "docker_networks": [{"name": "foo"}],
                    }
                ],
            },
            False,
        ),
        # Podman-only option must be rejected
        (
            {
                "driver": {"name": "containers"},
                "platforms": [
                    {"name": "instance", "image": "image:tag", "systemd": "true"}
                ],
            },
            False,
        ),
        # "unless-stopped" is docker-only and not portable across backends
        (
            {
                "driver": {"name": "containers"},
                "platforms": [
                    {
                        "name": "instance",
                        "image": "image:tag",
                        "restart_policy": "unless-stopped",
                    }
                ],
            },
            False,
        ),
        # A list of commands is podman-only; the portable form is a string
        (
            {
                "driver": {"name": "containers"},
                "platforms": [
                    {
                        "name": "instance",
                        "image": "image:tag",
                        "command": ["sleep", "infinity"],
                    }
                ],
            },
            False,
        ),
        # registry.credentials.email is docker-only and not portable
        (
            {
                "driver": {"name": "containers"},
                "platforms": [
                    {
                        "name": "instance",
                        "image": "image:tag",
                        "registry": {
                            "url": "registry.example.com",
                            "credentials": {
                                "username": "u",
                                "password": "p",
                                "email": "u@example.com",
                            },
                        },
                    }
                ],
            },
            False,
        ),
    ],
)
def test_container_driver_schema_validation(config, valid):
    """Asserts that the containers driver schema accepts/rejects configs correctly."""
    schema_file = api.drivers()["containers"].schema_file()
    schema = json.loads(Path(schema_file).read_text())
    if valid:
        validate(instance=config, schema=schema)
    else:
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)
