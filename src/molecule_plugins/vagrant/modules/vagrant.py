#!/usr/bin/python

#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.


import contextlib
import copy
import datetime
import os
import subprocess
import sys
from collections.abc import MutableMapping

import jinja2
from ansible.module_utils.basic import AnsibleModule

try:
    import vagrant
except ImportError:
    sys.exit("ERROR: Driver missing, install python-vagrant.")
ANSIBLE_METADATA = {
    "metadata_version": "0.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: vagrant
short_description: Manage Vagrant instances
description:
  - Manage the life cycle of Vagrant instances.
version_added: 2.0
author:
  - Cisco Systems, Inc.
options:
  instances:
    description:
      - list of instances to handle
    required: False
    default: []
  instance_name:
    description:
      - Assign a name to a new instance or match an existing instance.
    required: False
    default: None
  instance_interfaces:
    description:
      - Assign interfaces to a new instance.
    required: False
    default: []
  instance_raw_config_args:
    description:
      - Additional Vagrant options not explicitly exposed by this module.
    required: False
    default: None
  config_options:
    description:
      - Additional config options not explicitly exposed by this module.
    required: False
    default: {}
  platform_box:
    description:
      - Name of Vagrant box.
    required: True
    default: None
  platform_box_version:
    description:
      - Explicit version of Vagrant box to use.
    required: False
    default: None
  platform_box_url:
    description:
      - The URL to a Vagrant box.
    required: False
    default: None
  platform_box_download_checksum:
    description:
      - The checksum of the box specified by platform_box_url.
    required: False
    default: None
  platform_box_download_checksum_type:
    description:
      - The type of checksum specified by platform_box_download_checksum (if any).
    required: False
    default: None
  provider_name:
    description:
      - Name of the Vagrant provider to use.
    required: False
    default: virtualbox
  provider_memory:
    description:
      - Amount of memory to allocate to the instance.
    required: False
    default: 512
  provider_cpus:
    description:
      - Number of CPUs to allocate to the instance.
    required: False
    default: 2
  provider_options:
    description:
      - Additional provider options not explicitly exposed by this module.
    required: False
    default: {}
  provider_override_args:
    description:
      - Additional override options not explicitly exposed by this module.
    required: False
    default: None
  provider_raw_config_args:
    description:
      - Additional Vagrant options not explicitly exposed by this module.
    required: False
    default: None
  force_stop:
    description:
      - Force halt the instance, then destroy the instance.
    required: False
    default: False
  state:
    description:
      - The desired state of the instance.
    required: True
    choices: ['up', 'halt', 'destroy']
    default: None
  workdir:
    description:
      - vagrant working directory
    required: False
    default: content of MOLECULE_EPHEMERAL_DIRECTORY environment variable
  default_box:
    description:
      - Default vagrant box to use when not specified in instance configuration
    required: False
    default: None
  cachier:
    description:
      - Cachier scope configuration. Can be "machine" or "box". Any other value
        will disable cachier.
    required: False
    default: "machine"
  parallel:
    description:
      - Enable or disable parallelism when bringing up the VMs by
        setting VAGRANT_NO_PARALLEL environment variable.
    required: False
    default: True

requirements:
    - python >= 2.6
    - python-vagrant
    - vagrant
"""

EXAMPLES = """
See doc/source/configuration.rst
"""

VAGRANTFILE_TEMPLATE = """
{%- macro ruby_format(value) -%}
  {%- if value is boolean -%}
    {{ value | string | lower }}
  {%- elif value is string -%}
    {# "Bug" compat. To be removed later #}
    {%- if value[0] == value[-1] and value.startswith(("'", '"')) -%}
    {{ value }}
    {%- else -%}
    "{{ value }}"
    {%- endif -%}
  {%- else -%}
    {{ value }}
  {%- endif -%}
{%- endmacro -%}

{%- macro dict2args(dictionary) -%}
  {% set sep = joiner(", ") %}
  {%- for key, value in dictionary.items() -%}
    {{ sep() }}{{ key }}: {{ ruby_format(value) }}
  {%- endfor -%}
{%- endmacro -%}

# Ansible managed

Vagrant.configure('2') do |config|
  if Vagrant.has_plugin?('vagrant-cachier')
    {% if cachier is not none and cachier in [ "machine", "box" ] %}
    config.cache.scope = '{{ cachier }}'
    {% else %}
    config.cache.disable!
    {% endif %}
  end

{% for instance in instances %}
  config.vm.define "{{ instance.name }}" do |c|
    ##
    # Box definition
    ##
    c.vm.box = "{{ instance.box }}"
    {{ 'c.vm.box_version = "{}"'.format(instance.box_version) | safe if instance.box_version }}
    {{ 'c.vm.box_url = "{}"'.format(instance.box_url) | safe if instance.box_url }}
    {{ 'c.vm.box_download_checksum = "{}"'.format(instance.box_download_checksum) | safe if instance.box_download_checksum }}
    {{ 'c.vm.box_download_checksum_type = "{}"'.format(instance.box_download_checksum_type) | safe if instance.box_download_checksum_type }}

    ##
    # Config options
    ##
    {% if instance.config_options['synced_folder'] is sameas false %}
    c.vm.synced_folder ".", "/vagrant", disabled: true
    {% endif %}

    {% for k,v in instance.config_options.items() %}
    {% if k not in ['synced_folder', 'cachier'] %}c.{{ k }} = {{ ruby_format(v) }}{% endif %}
    {% endfor %}

    {% if instance.hostname is boolean and instance.hostname is sameas false %}
    # c.vm.hostname not set
    {% elif instance.hostname is string %}
    c.vm.hostname = "{{ instance.hostname }}"
    {% else %}
    c.vm.hostname = "{{ instance.name }}"
    {% endif %}

    ##
    # Network
    ##
    {% for n in instance.networks %}
    c.vm.network "{{ n.name }}", {{ dict2args(n.options) }}
    {% endfor %}

    ##
    # instance_raw_config_args
    ##
    {% if instance.instance_raw_config_args is not none %}{% for arg in instance.instance_raw_config_args -%}
    c.{{ arg | safe }}
    {% endfor %}{% endif %}

    ##
    # Provider
    ##
    c.vm.provider "{{ instance.provider }}" do |{{ instance.provider | lower }}, override|
      {% if instance.provider == "vsphere" %}
      {{ instance.provider | lower }}.memory_mb = {{ instance.memory }}
      {{ instance.provider | lower }}.cpu_count = {{ instance.cpus }}
      {% elif instance.provider == 'vmware_esxi' %}
      {{ instance.provider | lower }}.guest_memsize = {{ instance.memory }}
      {{ instance.provider | lower }}.guest_numvcpus = {{ instance.cpus }}
      {% elif instance.provider.startswith('vmware_') %}
      {{ instance.provider | lower }}.vmx['memsize'] = {{ instance.memory }}
      {{ instance.provider | lower }}.vmx['numvcpus'] = {{ instance.cpus }}
      {% else %}
      {{ instance.provider | lower }}.memory = {{ instance.memory }}
      {{ instance.provider | lower }}.cpus = {{ instance.cpus }}
      {% endif %}

      {% for option, value in instance.provider_options.items() %}
      {{ instance.provider | lower }}.{{ option }} = {{ ruby_format(value) }}
      {% endfor %}

      {% if instance.provider_raw_config_args is not none %}
        {% for arg in instance.provider_raw_config_args %}
      {{ instance.provider | lower }}.{{ arg | safe }}
        {% endfor %}
      {% endif %}

      {% if instance.provider_override_args is not none %}
        {% for arg in instance.provider_override_args -%}
      override.{{ arg | safe }}
        {% endfor %}
      {% endif %}

      {% if instance.provider == 'virtualbox' %}
      {% if 'linked_clone' not in instance.provider_options %}
      virtualbox.linked_clone = true
      {% endif %}
      {% endif %}
      {% if instance.provider == 'libvirt' %}
        {% if no_kvm is sameas true and 'driver' not in instance.provider_options %}
      libvirt.driver='qemu'
        {% endif %}
        {% set libvirt_use_qemu = no_kvm %}
        {% if 'driver' in instance.provider_options and 'qemu' in instance.provider_options['driver'] %}
          {% set libvirt_use_qemu = true %}
        {% endif %}
        {% if libvirt_use_qemu is sameas true %}
          {% if 'cpu_mode' not in instance.provider_options %}
      # When using qemu instead of kvm, some libvirt systems
      # will use EPYC as vCPU model inside the new VM.
      # This will lead to process hang with ssh-keygen -A on alpine.
      # Not sure were the bug is (libvirt or qemu or alpine or all of them) but using QEMU64
      # cpu model will work around this. Hopefully, by checking 'cpu_mode' option, it will
      # allow people to override the model to use.
      libvirt.cpu_mode = 'custom'
      libvirt.cpu_model = 'qemu64'
          {% endif %}
        {% endif %}
      {% endif %}
    end
  end
{% endfor %}
end
""".strip()

RETURN = r"""
rc:
    description: The command return code (0 means success)
    returned: always
    type: int
cmd:
    description: The command executed by the task
    returned: always
    type: str
stdout:
    description: The command standard output
    returned: changed
    type: str
stderr:
    description: Output on stderr
    returned: changed
    type: str
"""


# Taken from molecule.util.
def merge_dicts(a: MutableMapping, b: MutableMapping) -> MutableMapping:
    """Merge the values of b into a and returns a new dict.

    This function uses the same algorithm as Ansible's `combine(recursive=True)` filter.

    :param a: the target dictionary
    :param b: the dictionary to import
    :return: dict
    """
    result = copy.deepcopy(a)

    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            result[k] = merge_dicts(a[k], v)
        else:
            result[k] = v

    return result


class VagrantClient:
    def __init__(self, module) -> None:
        self._module = module
        self.provision = self._module.params["provision"]
        self.cachier = self._module.params["cachier"]

        # compat
        if self._module.params["instance_name"] is not None:
            self._module.warn(
                "Please convert your playbook to use the instances parameter. Compat layer will be removed later.",
            )
            self.instances = [
                {
                    "name": self._module.params["instance_name"],
                    "interfaces": self._module.params["instance_interfaces"],
                    "instance_raw_config_args": self._module.params[
                        "instance_raw_config_args"
                    ],
                    "config_options": self._module.params["config_options"],
                    "box": self._module.params["platform_box"],
                    "box_version": self._module.params["platform_box_version"],
                    "box_url": self._module.params["platform_box_url"],
                    "box_download_checksum": self._module.params[
                        "platform_box_download_checksum"
                    ],
                    "box_download_checksum_type": self._module.params[
                        "platform_box_download_checksum_type"
                    ],
                    "memory": self._module.params["provider_memory"],
                    "cpus": self._module.params["provider_cpus"],
                    "provider_options": self._module.params["provider_options"],
                    "provider_override_args": self._module.params[
                        "provider_override_args"
                    ],
                    "provider_raw_config_args": self._module.params[
                        "provider_raw_config_args"
                    ],
                },
            ]
        else:
            self.instances = self._module.params["instances"]

        self._config = self._get_config()
        self._vagrantfile = self._config["vagrantfile"]
        self._vagrant = self._get_vagrant()
        self._write_configs()
        self._has_error = None
        self._datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.result = {}

    @contextlib.contextmanager
    def stdout_cm(self):
        """Redirect the stdout to a log file."""
        with open(self._get_stdout_log(), "a+") as fh:
            msg = f"### {self._datetime} ###\n"
            fh.write(msg)
            fh.flush()

            yield fh

    @contextlib.contextmanager
    def stderr_cm(self):
        """Redirect the stderr to a log file."""
        with open(self._get_stderr_log(), "a+") as fh:
            msg = f"### {self._datetime} ###\n"
            fh.write(msg)
            fh.flush()

            try:
                yield fh
            except subprocess.CalledProcessError as e:
                self._has_error = True
                self.result["cmd"] = e.cmd
                self.result["rc"] = e.returncode
                self.result["stderr"] = e.output or ""

                # raise
            except Exception as e:
                self._has_error = True
                if hasattr(e, "message"):
                    fh.write(e.message)
                else:
                    fh.write(e)
                fh.flush()
                raise

    def up(self):
        changed = False
        if self._running() != len(self.instances):
            changed = True
            provision = self.provision
            with contextlib.suppress(Exception):
                self._vagrant.up(provision=provision)

        # NOTE(retr0h): Ansible wants only one module return `fail_json`
        # or `exit_json`.
        if not self._has_error:
            # compat
            if self._module.params["instance_name"] is not None:
                self._module.exit_json(
                    changed=changed,
                    log=self._get_stdout_log(),
                    **self._conf()[0],
                )
            self._module.exit_json(
                changed=changed,
                log=self._get_stdout_log(),
                results=self._conf(),
            )

        msg = f"Failed to start the VM(s): See log file '{self._get_stderr_log()}'"
        with open(self._get_stderr_log(), encoding="utf-8") as f:
            self.result["stderr"] = f.read()
        self._module.fail_json(msg=msg, **self.result)

    def destroy(self):
        changed = False
        if self._created() > 0:
            changed = True
            if self._module.params["force_stop"]:
                self._vagrant.halt(force=True)
            self._vagrant.destroy()

        self._module.exit_json(changed=changed)

    def halt(self):
        changed = False
        if self._running() > 0:
            changed = True
            self._vagrant.halt(force=self._module.params["force_stop"])

        self._module.exit_json(changed=changed)

    def _conf_instance(self, instance_name):
        try:
            return self._vagrant.conf(vm_name=instance_name)
        except Exception:
            msg = "Failed to get vagrant config for {}: See log file '{}'".format(
                instance_name,
                self._get_stderr_log(),
            )
            with open(self._get_stderr_log(), encoding="utf-8") as f:
                self.result["stderr"] = f.read()
                self._module.fail_json(msg=msg, **self.result)

    def _status_instance(self, instance_name):
        try:
            s = self._vagrant.status(vm_name=instance_name)[0]

            return {"name": s.name, "state": s.state, "provider": s.provider}
        except Exception:
            msg = "Failed to get status for {}: See log file '{}'".format(
                instance_name,
                self._get_stderr_log(),
            )
            with open(self._get_stderr_log(), encoding="utf-8") as f:
                self.result["stderr"] = f.read()
                self._module.fail_json(msg=msg, **self.result)

    def _conf(self):
        conf = []

        for i in self.instances:
            instance_name = i["name"]
            c = self._conf_instance(instance_name)
            if c:
                conf.append(c)

        return conf

    def _status(self):
        vms_status = []

        for i in self.instances:
            instance_name = i["name"]
            s = self._status_instance(instance_name)
            if s:
                vms_status.append(s)

        return vms_status

    def _created(self):
        status = self._status()
        if len(status) == 0:
            return 0

        count = sum(s["state"] == "not_created" for s in status)
        return len(status) - count

    def _running(self):
        status = self._status()
        if len(status) == 0:
            return 0

        count = sum(s["state"] == "running" for s in status)
        return count

    def _get_config(self):
        conf = {}
        conf["workdir"] = os.getenv("MOLECULE_EPHEMERAL_DIRECTORY")
        if self._module.params["workdir"] is not None:
            conf["workdir"] = self._module.params["workdir"]
        if conf["workdir"] is None:
            self._module.fail_json(
                msg="Either workdir parameter or MOLECULE_EPHEMERAL_DIRECTORY env variable has to be set",
            )
        conf["vagrantfile"] = os.path.join(conf["workdir"], "Vagrantfile")
        return conf

    def _write_vagrantfile(self):
        instances = self._get_vagrant_config_dict()
        j_env = jinja2.Environment(autoescape=True)
        t = j_env.from_string(VAGRANTFILE_TEMPLATE)
        template = t.render(
            instances=instances,
            cachier=self.cachier,
            no_kvm=not os.path.exists("/dev/kvm"),
        )
        with open(self._vagrantfile, "w") as f:
            f.write(template)

    def _write_configs(self):
        self._write_vagrantfile()
        try:
            self._vagrant.validate(self._config["workdir"])
        except subprocess.CalledProcessError as e:
            self._module.fail_json(
                msg=f"Failed to validate generated Vagrantfile: {e.stderr}",
            )

    def _get_vagrant(self):
        vagrant_env = os.environ.copy()
        if self._module.params["parallel"] is False:
            vagrant_env["VAGRANT_NO_PARALLEL"] = "1"
        v = vagrant.Vagrant(
            out_cm=self.stdout_cm,
            err_cm=self.stderr_cm,
            root=self._config["workdir"],
            env=vagrant_env,
        )

        return v

    def _get_instance_vagrant_config_dict(self, instance):
        checksum = instance.get("box_download_checksum")
        checksum_type = instance.get("box_download_checksum_type")
        if bool(checksum) ^ bool(checksum_type):
            self._module.fail_json(
                msg="box_download_checksum and box_download_checksum_type must be used together",
            )

        networks = []
        if "interfaces" in instance:
            for iface in instance["interfaces"]:
                net = {}
                net["name"] = iface["network_name"]
                iface.pop("network_name")
                net["options"] = iface
                networks.append(net)

        # compat
        provision = instance.get("provision")
        if provision is not None:
            self.provision = self.provision or provision
            self._module.warn(
                "Please convert your molecule.yml to move provision parameter to driver:. Compat layer will be removed later.",
            )
        d = {
            "name": instance.get("name"),
            "hostname": instance.get("hostname", instance.get("name")),
            "memory": instance.get("memory", 512),
            "cpus": instance.get("cpus", 2),
            "networks": networks,
            "instance_raw_config_args": instance.get("instance_raw_config_args", None),
            "config_options": {
                # NOTE(retr0h): `synced_folder` does not represent the
                # actual key used by Vagrant.  Is used as a flag to
                # simply enable/disable shared folder.
                "synced_folder": False,
                "ssh.insert_key": True,
            },
            "box": instance.get("box", self._module.params["default_box"]),
            "box_version": instance.get("box_version"),
            "box_url": instance.get("box_url"),
            "box_download_checksum": checksum,
            "box_download_checksum_type": checksum_type,
            "provider": self._module.params["provider_name"],
            "provider_options": {},
            "provider_raw_config_args": instance.get("provider_raw_config_args", None),
            "provider_override_args": instance.get("provider_override_args", None),
        }

        d["config_options"].update(
            merge_dicts(
                d["config_options"],
                instance.get("config_options", {}),
            ),
        )
        if "cachier" in d["config_options"]:
            self.cachier = d["config_options"]["cachier"]
            self._module.warn(
                "Please convert your molecule.yml to move cachier parameter to driver:. Compat layer will be removed later.",
            )

        d["provider_options"].update(
            merge_dicts(
                d["provider_options"],
                instance.get("provider_options", {}),
            ),
        )

        return d

    def _get_vagrant_config_dict(self):
        config_list = [
            self._get_instance_vagrant_config_dict(instance)
            for instance in self.instances
        ]
        return config_list

    def _get_stdout_log(self):
        return self._get_vagrant_log("out")

    def _get_stderr_log(self):
        return self._get_vagrant_log("err")

    def _get_vagrant_log(self, __type):
        return os.path.join(self._config["workdir"], f"vagrant.{__type}")


def main():
    module = AnsibleModule(
        argument_spec={
            "instances": {"type": "list", "required": False},
            "instance_name": {"type": "str", "required": False, "default": None},
            "instance_interfaces": {"type": "list", "default": []},
            "instance_raw_config_args": {"type": "list", "default": None},
            "config_options": {"type": "dict", "default": {}},
            "platform_box": {"type": "str", "required": False},
            "platform_box_version": {"type": "str"},
            "platform_box_url": {"type": "str"},
            "platform_box_download_checksum": {"type": "str"},
            "platform_box_download_checksum_type": {"type": "str"},
            "provider_memory": {"type": "int", "default": 512},
            "provider_cpus": {"type": "int", "default": 2},
            "provider_options": {"type": "dict", "default": {}},
            "provider_override_args": {"type": "list", "default": None},
            "provider_raw_config_args": {"type": "list", "default": None},
            "provider_name": {"type": "str", "default": "virtualbox"},
            "default_box": {"type": "str", "default": None},
            "provision": {"type": "bool", "default": False},
            "force_stop": {"type": "bool", "default": False},
            "cachier": {"type": "str", "default": "machine"},
            "state": {
                "type": "str",
                "default": "up",
                "choices": ["up", "destroy", "halt"],
            },
            "workdir": {"type": "str"},
            "parallel": {"type": "bool", "default": True},
        },
        required_together=[
            ("platform_box_download_checksum", "platform_box_download_checksum_type"),
            ("instances", "default_box"),
        ],
        supports_check_mode=False,
    )

    if not (bool(module.params["instances"]) ^ bool(module.params["instance_name"])):
        module.fail_json(
            msg="Either instances or instance_name parameters should be used and not at the same time",
        )

    v = VagrantClient(module)

    if module.params["state"] == "up":
        v.up()

    if module.params["state"] == "destroy":
        v.destroy()

    if module.params["state"] == "halt":
        v.halt()

    module.fail_json(msg="Unknown error", **v.result)


if __name__ == "__main__":
    main()
