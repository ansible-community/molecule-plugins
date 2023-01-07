***********************
Molecule Vagrant Plugin
***********************

.. image:: https://badge.fury.io/py/molecule-vagrant.svg
   :target: https://badge.fury.io/py/molecule-vagrant
   :alt: PyPI Package

.. image:: https://zuul-ci.org/gated.svg
   :target: https://dashboard.zuul.ansible.com/t/ansible/builds?project=ansible-community/molecule-vagrant

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/python/black
   :alt: Python Black Code Style

.. image:: https://img.shields.io/badge/Code%20of%20Conduct-silver.svg
   :target: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
   :alt: Ansible Code of Conduct

.. image:: https://img.shields.io/badge/Mailing%20lists-silver.svg
   :target: https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information
   :alt: Ansible mailing lists

.. image:: https://img.shields.io/badge/license-MIT-brightgreen.svg
   :target: LICENSE
   :alt: Repository License

Molecule Vagrant is designed to allow use of Vagrant for provisioning of test
resources.

Supported Platforms
===================

This driver relies on vagrant command line which is known to be problematic
to install on several platforms. We do our best to perform CI/CD testing on
multiple platforms but some are disabled due to known bugs.

* ✅ MacOS with VirtualBox - GitHub Actions
* ✅ Fedora 32 with libvirt - Zuul
* ✅ Ubuntu Bionic (18.04) with libvirt - Zuul
* ❌ CentOS 8 with libvirt - Zuul DISABLED due to 1127_ and 11020_

Please **do not file bugs for unsupported platforms**. You are welcomed to
create PRs that fix untested platform, as long they do not break existing ones.

.. _`1127`: https://github.com/vagrant-libvirt/vagrant-libvirt/issues/1127
.. _`11020`: https://github.com/hashicorp/vagrant/issues/11020


Documentation
=============

To use this plugin, you'll need to set the ``driver`` and ``platform``
variables in your ``molecule.yml``. Here's a simple example using the
`fedora/32-cloud-base`_ box:

.. code-block:: yaml

   driver:
     name: vagrant

   platforms:
     - name: instance
       box: fedora/32-cloud-base
       memory: 512
       cpus: 1

Here's a full example with the libvirt provider:

.. code-block:: yaml

   driver:
     name: vagrant
     provider:
       # Can be any supported provider (virtualbox, parallels, libvirt, etc)
       # Defaults to virtualbox
       name: libvirt
     # Run vagrant up with --provision.
     # Defaults to --no-provision)
     provision: no
     # vagrant-cachier configuration
     # Defaults to 'machine'
     # Any value different from 'machine' or 'box' will disable it
     cachier: machine
     # If set to false, set VAGRANT_NO_PARALLEL to '1'
     # Defaults to true
     parallel: true
     # vagrant box to use by default
     # Defaults to 'generic/alpine316'
     default_box: 'generic/alpine316'

   platforms:
     - name: instance
       # If specified, set host name to hostname, unless it's set to False and
       # the host name won't be set. In all other cases (including default) use
       # 'name' as host name.
       hostname: foo.bar.com
       # List of dictionaries mapped to `config.vm.network`
       interfaces:
         # `network_name` is the required identifier, all other keys map to
         # arguments.
         - auto_config: true
           network_name: private_network
           type: dhcp
         - network_name: private_network
           ip: 192.168.123.3
         - network_name: forwarded_port
           guest: 80
           host: 8080
       # List of raw Vagrant `config` options
       instance_raw_config_args:
         # use single quotes to avoid YAML parsing as dict due to ':'
         - 'vm.synced_folder ".", "/vagrant", type: "rsync"'
         # Run 'uname' a provisionning step **needs 'provision: true' to work**
         - 'vm.provision :shell, inline: "uname"'
       # Dictionary of `config` options. Note that string values need to be
       # explicitly enclosed in quotes.
       config_options:
         ssh.keep_alive: yes
         ssh.remote_user: 'vagrant'
         synced_folder: true
       box: fedora/32-cloud-base
       box_version: 32.20200422.0
       box_url:
       memory: 512
       cpus: 1
       # Dictionary of options passed to the provider
       provider_options:
         video_type: 'vga'
       # List of raw provider options
       provider_raw_config_args:
         - cpuset = '1-4,^3,6'

.. _`fedora/32-cloud-base`: https://app.vagrantup.com/fedora/boxes/32-cloud-base


More examples may be found in the ``molecule`` `scenarios directory`_.
They're the scenarios used by the CI.


.. _get-involved:

Get Involved
============

* Join us in the ``#ansible-devtools`` channel on `Libera`_.
* Join the discussion in `molecule-users Forum`_.
* Join the community working group by checking the `wiki`_.
* Want to know about releases, subscribe to `ansible-announce list`_.
* For the full list of Ansible email Lists, IRC channels see the
  `communication page`_.

.. _`Libera`: https://web.libera.chat/?channel=#ansible-devtools
.. _`molecule-users Forum`: https://groups.google.com/forum/#!forum/molecule-users
.. _`wiki`: https://github.com/ansible/community/wiki/Molecule
.. _`ansible-announce list`: https://groups.google.com/group/ansible-announce
.. _`communication page`: https://docs.ansible.com/ansible/latest/community/communication.html
.. _`scenarios directory`: https://github.com/ansible-community/molecule-vagrant/tree/main/molecule_vagrant/test/scenarios/molecule
.. _authors:

Authors
=======

Molecule Vagrant Plugin was created by Sorin Sbarnea based on code from
Molecule.

.. _license:

License
=======

The `MIT`_ License.

.. _`MIT`: https://github.com/ansible-community/molecule-vagrant/blob/main/LICENSE

The logo is licensed under the `Creative Commons NoDerivatives 4.0 License`_.

If you have some other use in mind, contact us.

.. _`Creative Commons NoDerivatives 4.0 License`: https://creativecommons.org/licenses/by-nd/4.0/
