# Copyright (c) 2015-2018 Cisco Systems, Inc.
# Copyright (c) 2018 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Unit tests for the podman driver resource-limit platform options."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import pytest
import yaml

from jsonschema import ValidationError, validate

from molecule import api


CREATE_PLAYBOOK = (
    Path(__file__).parents[2] / "src" / "molecule_plugins" / "podman" / "playbooks" / "create.yml"
)

RESOURCE_LIMIT_PLATFORM = {
    "name": "instance",
    "image": "image:tag",
    "memory": "268435456",
    "memory_swap": "536870912",
    "pids_limit": "1234",
}


@pytest.fixture()
def schema(driver_name: str) -> dict[str, Any]:
    """Return the podman driver JSON schema.

    Args:
        driver_name: Name of the driver under test.

    Returns:
        The parsed driver JSON schema.
    """
    schema_file = api.drivers()[driver_name].schema_file()
    return json.loads(Path(schema_file).read_text())


def _create_task() -> dict[str, Any]:
    """Return the ``Create molecule instance(s)`` task of the bundled playbook.

    Returns:
        The task that calls ``containers.podman.podman_container``.
    """
    playbook = yaml.safe_load(CREATE_PLAYBOOK.read_text())
    tasks = [task for play in playbook for task in play.get("tasks", []) if isinstance(task, dict)]
    matches = [
        task for task in tasks if isinstance(task.get("containers.podman.podman_container"), dict)
    ]
    assert len(matches) == 1, "expected exactly one podman_container task"
    return matches[0]["containers.podman.podman_container"]


def test_resource_limits_are_accepted_by_schema(schema: dict[str, Any]) -> None:
    """Asserts that memory, memory_swap and pids_limit validate as strings.

    Args:
        schema: The podman driver JSON schema.
    """
    config = {"driver": {"name": "podman"}, "platforms": [dict(RESOURCE_LIMIT_PLATFORM)]}
    validate(instance=config, schema=schema)
    assert config["platforms"][0]["pids_limit"] == "1234"


def test_resource_limits_reject_integer_types(schema: dict[str, Any]) -> None:
    """Asserts that integer resource limits are rejected to maintain argument spec parity.

    Args:
        schema: The podman driver JSON schema.
    """
    for field in ("memory", "memory_swap", "pids_limit"):
        config = {
            "driver": {"name": "podman"},
            "platforms": [
                {
                    "name": "instance",
                    "image": "image:tag",
                    field: 1234,
                },
            ],
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)


def test_resource_limits_accept_size_strings(schema: dict[str, Any]) -> None:
    """Asserts that podman size strings are accepted as well as byte counts.

    Args:
        schema: The podman driver JSON schema.
    """
    config = {
        "driver": {"name": "podman"},
        "platforms": [
            {
                "name": "instance",
                "image": "image:tag",
                "memory": "256m",
                "memory_swap": "512m",
                "pids_limit": "-1",
            },
        ],
    }
    validate(instance=config, schema=schema)


def test_create_playbook_forwards_resource_limits() -> None:
    """Asserts that the create playbook passes the limits to the module."""
    task = _create_task()
    for key in ("memory", "memory_swap", "pids_limit"):
        expected = "{{ item." + key + " | default(omit) }}"
        assert task[key] == expected


def test_create_playbook_keeps_existing_parameters() -> None:
    """Asserts that unrelated container parameters are untouched."""
    task = _create_task()
    for key in ("ulimits", "privileged", "pid"):
        assert key in task
