"""Openstack Driver Module."""

import os
from importlib import import_module

from molecule import logger, util
from molecule.api import Driver

LOG = logger.get_logger(__name__)


class Openstack(Driver):
    """
    Openstack Driver Class.

    The class responsible for managing `Openstack`_ instances.  `Openstack`_ is
    `not` the default driver used in Molecule.

    .. _`openstack_collection`: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/index.html

    .. code-block:: yaml

        driver:
          name: openstack
        platforms:
          - name: instance-1
            flavor: m1.small
            image: Ubuntu_20.04
            user: ubuntu
            security_group:
                name: molecule-sec
                description: Molecule test
                rules:
                  - proto: tcp
                    port_min: 22
                    port_max: 80
                    cidr: 0.0.0.0/0
                  - proto: icmp
                    port: -1
                    cidr: 0.0.0.0/0
                  - proto: tcp
                    port: 22
                    type: IPv6
                    cidr: ::/0
            network:
                name: network1
                create: true # default
                router:
                    name: router1
                    ext_network: public
                    subnet: subnet1 # must match with network.subnet.name
                subnet:
                    name: subnet1 # must match with network.router.subnet
                    cidr: 192.168.10.0/24
                    ipv: 4
                    dns_nameservers:
                        - 8.8.8.8
                    host_routes:
                        - destination: 192.168.0.0/24
                        nexthop: 192.168.0.1
          - name: instance-2
            flavor: m1.small
            image: Ubuntu_20.04
            user: ubuntu
            security_group:
                name: molecule-sec # use security group from instance-1
            network:
                name: network1 # use network from instance-1

    If specifying the security_group in your platform configuration, the security group is created.
    You can disable this behavior by specifying security_group.create = false.
    In this case the security group must exist.

    .. code-block:: yaml

        driver:
          name: openstack
        platforms:
          - name: instance-1
            flavor: m1.small
            image: Ubuntu_20.04
            user: ubuntu
            security_group:
                name: molecule-sec
                create: false

    .. code-block:: bash

        $ python3 -m pip install molecule-plugins[openstack]

    Change the options passed to the ssh client.

    .. code-block:: yaml

        driver:
          name: openstack
          ssh_connection_options:
            - '-o ControlPath=~/.ansible/cp/%r@%h-%p'

    .. important::

        Molecule does not merge lists, when overriding the developer must
        provide all options.
    """

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self._name = "openstack"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def login_cmd_template(self):
        connection_options = " ".join(self.ssh_connection_options)

        return (
            "ssh {address} "
            "-l {user} "
            "-p {port} "
            "-i {identity_file} "
            f"{connection_options}"
        )

    @property
    def default_safe_files(self):
        return [self.instance_config]

    @property
    def default_ssh_connection_options(self):
        return self._get_ssh_connection_options()

    def login_options(self, instance_name):
        d = {"instance": instance_name}

        return util.merge_dicts(d, self._get_instance_config(instance_name))

    def ansible_connection_options(self, instance_name):
        try:
            d = self._get_instance_config(instance_name)

            return {
                "ansible_user": d["user"],
                "ansible_host": d["address"],
                "ansible_port": d["port"],
                "ansible_private_key_file": d["identity_file"],
                "connection": "ssh",
                "ansible_ssh_common_args": " ".join(self.ssh_connection_options),
            }
        except StopIteration:
            return {}
        except OSError:
            # Instance has yet to be provisioned , therefore the
            # instance_config is not on disk.
            return {}

    def _get_instance_config(self, instance_name):
        instance_config_dict = util.safe_load_file(self._config.driver.instance_config)

        return next(
            item for item in instance_config_dict if item["instance"] == instance_name
        )

    def _is_module_installed(self, module_name):
        try:
            import_module(module_name)
            return True
        except ModuleNotFoundError:
            return False

    def sanity_checks(self):
        req_modules = {"openstack": "openstacksdk"}
        for module, pkg in req_modules.items():
            if not self._is_module_installed(module):
                util.sysexit_with_message(
                    f'"{module}" not installed: pip install {pkg} should fix it.',
                )

    def template_dir(self):
        """Return path to its own cookiecutterm templates. It is used by init
        command in order to figure out where to load the templates from.
        """
        return os.path.join(os.path.dirname(__file__), "cookiecutter")

    @property
    def required_collections(self) -> dict[str, str]:
        """Return collections dict containing names and versions required."""
        return {"openstack.cloud": "2.1.0"}
