# Copyright (c) 2022 Community managed Ansible repositories

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

"""Unit tests for the podman driver ``tmpfs`` platform option."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import pytest
import yaml

from jsonschema import ValidationError, validate

from molecule import api


TMPFS_DICT_YAML = """
tmpfs:
  /tmp: "rw,size=787448k,mode=1777"
  /run: "rw"
"""

TMPFS_LIST_YAML = """
tmpfs:
  - /tmp:rw,size=787448k,mode=1777
  - /run:rw
"""


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


def _config(tmpfs_yaml: str) -> dict[str, Any]:
    """Build a minimal molecule config whose platform uses the given tmpfs.

    Args:
        tmpfs_yaml: YAML snippet holding the ``tmpfs`` key of a platform.

    Returns:
        A molecule config with a single podman platform.
    """
    platform = {"name": "instance", "image": "image:tag"}
    platform.update(yaml.safe_load(tmpfs_yaml))
    return {"driver": {"name": "podman"}, "platforms": [platform]}


def test_tmpfs_dict_form_is_accepted(schema: dict[str, Any]) -> None:
    """Asserts that tmpfs declared as a mapping of mount point to options is valid.

    Args:
        schema: The podman driver JSON schema.
    """
    config = _config(TMPFS_DICT_YAML)
    assert config["platforms"][0]["tmpfs"] == {
        "/tmp": "rw,size=787448k,mode=1777",
        "/run": "rw",
    }
    validate(instance=config, schema=schema)


def test_tmpfs_list_form_is_rejected(schema: dict[str, Any]) -> None:
    """Asserts that the previous list form of tmpfs is no longer accepted.

    Args:
        schema: The podman driver JSON schema.
    """
    config = _config(TMPFS_LIST_YAML)
    assert isinstance(config["platforms"][0]["tmpfs"], list)
    with pytest.raises(ValidationError, match="is not of type 'object'"):
        validate(instance=config, schema=schema)


@pytest.mark.parametrize(
    "value",
    [123, True, ["rw"], {"mode": "1777"}, None],
    ids=["int", "bool", "list", "dict", "null"],
)
def test_tmpfs_non_string_value_is_rejected(schema: dict[str, Any], value: object) -> None:
    """Asserts that tmpfs mount options must be strings.

    Args:
        schema: The podman driver JSON schema.
        value: A non-string mount option value.
    """
    config = _config("tmpfs: {}")
    config["platforms"][0]["tmpfs"] = {"/tmp": value}
    with pytest.raises(ValidationError, match="is not of type 'string'"):
        validate(instance=config, schema=schema)
