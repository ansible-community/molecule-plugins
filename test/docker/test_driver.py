"""Unit tests."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError, validate

from molecule import api


def test_docker_driver_is_detected(driver_name: str):
    """Asserts that molecule recognizes the driver."""
    assert driver_name in [str(d) for d in api.drivers()]


def test_docker_driver_provides_schema(driver_name: str):
    """Asserts that the docker driver provides a JSON schema file."""
    driver = api.drivers()[driver_name]
    schema_file = driver.schema_file()

    assert schema_file is not None
    assert Path(schema_file).is_file()
    assert schema_file.endswith(driver_name + "/schema/driver.json")


def test_docker_driver_schema_is_valid(driver_name: str):
    """Asserts that the docker driver schema is a valid JSON Schema."""
    schema_file = api.drivers()[driver_name].schema_file()
    schema = json.loads(Path(schema_file).read_text())
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    ("config", "valid"),
    [
        # Minimal valid configuration
        (
            {
                "driver": {"name": "docker"},
                "platforms": [{"name": "instance", "image": "image:tag"}],
            },
            True,
        ),
        # Comprehensive configuration exercising all documented options
        (
            {
                "driver": {"name": "docker"},
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
                        "cgroupns_mode": "host",
                        "shm_size": "64M",
                        "devices": ["/dev/fuse:/dev/fuse:rwm"],
                        "volumes": ["/sys/fs/cgroup:/sys/fs/cgroup:ro"],
                        "keep_volumes": True,
                        "tmpfs": ["/tmp", "/run"],
                        "capabilities": ["SYS_ADMIN"],
                        "sysctls": {"net.core.somaxconn": 1024},
                        "exposed_ports": ["53/udp"],
                        "published_ports": ["0.0.0.0:8053:53/udp"],
                        "ulimits": ["nofile:262144:262144"],
                        "dns_servers": ["8.8.8.8"],
                        "etc_hosts": {"host1.example.com": "10.3.1.5"},
                        "docker_networks": [{"name": "foo"}],
                        "networks": [{"name": "foo"}],
                        "network_mode": "host",
                        "purge_networks": True,
                        "docker_host": "tcp://localhost:12376",
                        "cacert_path": "/foo/bar/ca.pem",
                        "cert_path": "/foo/bar/cert.pem",
                        "key_path": "/foo/bar/key.pem",
                        "tls_verify": True,
                        "env": {"FOO": "bar"},
                        "restart_policy": "unless-stopped",
                        "restart_retries": 1,
                        "buildargs": {"http_proxy": "http://proxy:8080/"},
                        "cache_from": ["registry.example.com/example:main"],
                        "user": "root",
                        "memory": "512m",
                        "platform": "linux/amd64",
                    }
                ],
            },
            True,
        ),
        # Podman-only options must be rejected
        (
            {
                "driver": {"name": "docker"},
                "platforms": [
                    {"name": "instance", "image": "image:tag", "systemd": "true"}
                ],
            },
            False,
        ),
    ],
)
def test_docker_driver_schema_validation(config, valid):
    """Asserts that the docker driver schema accepts/rejects configs correctly."""
    schema_file = api.drivers()["docker"].schema_file()
    schema = json.loads(Path(schema_file).read_text())
    if valid:
        validate(instance=config, schema=schema)
    else:
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)
