"""Openstack Driver Module."""

import os

from molecule import logger, util
from molecule.api import Driver
from importlib import import_module

LOG = logger.get_logger(__name__)

class Openstack(Driver):

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
            "ssh {{address}} "
            "-l {{user}} "
            "-p {{port}} "
            "-i {{identity_file}} "
            "{}"
        ).format(connection_options)
    
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
        req_modules = {'openstack': 'openstacksdk'}
        for module, pkg in req_modules.items():
            if not self._is_module_installed(module):
                util.sysexit_with_message(f'"{module}" not installed: pip install {pkg} should fix it.')
    
    def template_dir(self):
        """Return path to its own cookiecutterm templates. It is used by init
        command in order to figure out where to load the templates from.
        """
        return os.path.join(os.path.dirname(__file__), "cookiecutter")
    
    @property
    def required_collections(self) -> dict[str, str]:
        """Return collections dict containing names and versions required."""
        return {"openstack.cloud": "2.1.0"}
    