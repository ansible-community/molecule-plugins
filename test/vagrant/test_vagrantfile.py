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

"""Unit tests for Vagrantfile template rendering."""

from __future__ import annotations

from typing import Any

import jinja2
import pytest

from molecule_plugins.vagrant.modules.vagrant import VAGRANTFILE_TEMPLATE


def _render(instances: list[dict[str, Any]]) -> str:
    """Render VAGRANTFILE_TEMPLATE with the same Jinja environment the module uses.

    Args:
        instances: Instance dicts as produced by _get_vagrant_config_dict.

    Returns:
        The rendered Vagrantfile content.
    """
    env = jinja2.Environment(
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.from_string(VAGRANTFILE_TEMPLATE)
    return template.render(instances=instances, cachier="machine", no_kvm=False)


def _instance(networks: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a minimal instance dict for rendering.

    Args:
        networks: Network dicts with name and optional options keys.

    Returns:
        A template-ready instance dict.
    """
    return {
        "name": "instance-1",
        "hostname": "instance-1",
        "memory": 512,
        "cpus": 2,
        "networks": networks,
        "instance_raw_config_args": None,
        "config_options": {},
        "box": "generic/ubuntu2204",
        "box_version": None,
        "box_url": None,
        "box_architecture": None,
        "box_download_checksum": None,
        "box_download_checksum_type": None,
        "provider": "virtualbox",
        "provider_options": {},
        "provider_raw_config_args": None,
        "provider_override_args": None,
    }


@pytest.mark.parametrize(
    "networks",
    [
        pytest.param(
            [
                {"name": "private_network", "options": {"ip": "192.168.56.10"}},
                {"name": "public_network", "options": {"bridge": "en0"}},
            ],
            id="with-options",
        ),
        pytest.param(
            [{"name": "private_network"}, {"name": "public_network"}],
            id="without-options",
        ),
    ],
)
def test_multiple_networks_render_on_separate_lines(networks: list[dict[str, Any]]) -> None:
    """Regression test for https://github.com/ansible-community/molecule-plugins/issues/373.

    With trim_blocks=True, a trailing {% endif %} on the c.vm.network line
    swallowed the newline, merging consecutive network statements into one
    invalid Ruby line.

    Args:
        networks: Network dicts to render for a single instance.
    """
    rendered = _render([_instance(networks)])

    network_lines = [line for line in rendered.splitlines() if "c.vm.network" in line]

    assert len(network_lines) == 2
    for line in network_lines:
        assert line.count("c.vm.network") == 1
