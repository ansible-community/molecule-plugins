"""Lima Driver Module."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from shutil import which

from molecule import logger, util
from molecule.api import Driver
from molecule.util import sysexit_with_message

log = logger.get_logger(__name__)

LIMA_MINIMUM_VERSION = 2


class Lima(Driver):
    """
    Lima Driver Class.

    The class responsible for managing `Lima`_ virtual machines. `Lima`_ runs
    Linux virtual machines on Linux and macOS hosts and is `not` the default
    driver used in Molecule.

    Molecule leverages Ansible playbooks for Lima VM management, by mapping
    variables from ``molecule.yml`` into ``create.yml`` and ``destroy.yml``.

    .. code-block:: yaml

        driver:
          name: lima
        platforms:
          - name: instance
            lima_template: debian-12

    ``lima_template`` accepts a template name shipped with Lima, which is
    expanded to ``template:<name>``, or any other locator understood by
    ``limactl start``, such as a ``https://`` URL or a path to a local
    template file. Lima 2.0 or newer is required.

    .. code-block:: yaml

        platforms:
          - name: instance
            lima_template: https://example.com/lima.yaml
            cpus: 2
            memory: 4
            disk: 50

    ``cpus``, ``memory``, ``disk``, ``arch`` and ``vm_type`` are optional and
    map to the matching ``limactl start`` flags. Memory and disk are expressed
    in GiB. When omitted, the values from the template are used.

    Instances are started in plain mode, which disables mounts, port
    forwarding and containerd, leaving a VM reachable over SSH only.

    .. code-block:: bash

        $ python3 -m pip install 'molecule-plugins[lima]'

    Provide a list of files Molecule will preserve, relative to the scenario
    ephemeral directory, after any ``destroy`` subcommand execution.

    .. code-block:: yaml

        driver:
          name: lima
          safe_files:
            - foo

    .. _`Lima`: https://lima-vm.io/
    """

    _passed_sanity = False

    def __init__(self, config=None) -> None:
        """Construct Lima."""
        super().__init__(config)
        self._name = "lima"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def login_cmd_template(self):
        return "limactl shell {instance}"

    @property
    def default_safe_files(self):
        return []

    @property
    def default_ssh_connection_options(self):
        return self._get_ssh_connection_options()

    def login_options(self, instance_name):
        return {"instance": instance_name}

    def ansible_connection_options(self, instance_name):
        try:
            d = self._get_instance_config(instance_name)

            return {
                "ansible_user": d["user"],
                "ansible_host": d["address"],
                "ansible_port": d["port"],
                "ansible_private_key_file": d["identity_file"],
                "ansible_connection": "ssh",
                "ansible_ssh_common_args": " ".join(self.ssh_connection_options),
            }
        except StopIteration:
            return {}
        except OSError:
            # Instance has yet to be provisioned, therefore the
            # instance_config is not on disk.
            return {}

    def schema_file(self) -> str | None:
        """Return the path to the driver's JSON schema file."""
        p = Path(self._path, "schema", "driver.json")
        if p.is_file():
            return str(p)
        return None

    def sanity_checks(self):
        """Implement Lima driver sanity checks."""
        if self._passed_sanity:
            return

        log.info("Sanity checks: '%s'", self._name)

        if which("limactl") is None:
            sysexit_with_message(
                "limactl executable was not found, see https://lima-vm.io/ for "
                "installation instructions.",
            )

        try:
            result = subprocess.run(
                ["limactl", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            sysexit_with_message(f"Failed to execute limactl: {exc.stderr}")
        else:
            version = result.stdout.strip()
            log.info("Lima version: %s", version)

            major = _major_version(version)
            if major is not None and major < LIMA_MINIMUM_VERSION:
                sysexit_with_message(
                    f"Lima {LIMA_MINIMUM_VERSION}.0 or newer is required, "
                    f"found: {version}",
                )

            self._passed_sanity = True

    @property
    def required_collections(self) -> dict[str, str]:
        """Return collections dict containing names and versions required."""
        return {}

    def _get_instance_config(self, instance_name):
        instance_config_dict = util.safe_load_file(self._config.driver.instance_config)

        return next(
            item for item in instance_config_dict if item["instance"] == instance_name
        )


def _major_version(version: str) -> int | None:
    """Return the major version reported by limactl, when it can be parsed."""
    match = re.search(r"(\d+)\.\d+", version)
    if match is None:
        return None
    return int(match.group(1))
