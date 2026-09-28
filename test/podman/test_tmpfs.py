"""Unit tests for the podman driver ``tmpfs`` platform option."""

from __future__ import annotations

import json

from pathlib import Path

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
def schema(driver_name):
    """Return the podman driver JSON schema."""
    schema_file = api.drivers()[driver_name].schema_file()
    return json.loads(Path(schema_file).read_text())


def _config(tmpfs_yaml: str) -> dict:
    """Build a minimal molecule config whose platform uses the given tmpfs."""
    platform = {"name": "instance", "image": "image:tag"}
    platform.update(yaml.safe_load(tmpfs_yaml))
    return {"driver": {"name": "podman"}, "platforms": [platform]}


def test_tmpfs_dict_form_is_accepted(schema):
    """Asserts that tmpfs declared as a mapping of mount point to options is valid."""
    config = _config(TMPFS_DICT_YAML)
    assert config["platforms"][0]["tmpfs"] == {
        "/tmp": "rw,size=787448k,mode=1777",
        "/run": "rw",
    }
    validate(instance=config, schema=schema)


def test_tmpfs_list_form_is_rejected(schema):
    """Asserts that the previous list form of tmpfs is no longer accepted."""
    config = _config(TMPFS_LIST_YAML)
    assert isinstance(config["platforms"][0]["tmpfs"], list)
    with pytest.raises(ValidationError, match="is not of type 'object'"):
        validate(instance=config, schema=schema)


@pytest.mark.parametrize(
    "value",
    [123, True, ["rw"], {"mode": "1777"}, None],
    ids=["int", "bool", "list", "dict", "null"],
)
def test_tmpfs_non_string_value_is_rejected(schema, value):
    """Asserts that tmpfs mount options must be strings."""
    config = _config("tmpfs: {}")
    config["platforms"][0]["tmpfs"] = {"/tmp": value}
    with pytest.raises(ValidationError, match="is not of type 'string'"):
        validate(instance=config, schema=schema)
