*************************
Molecule Openstack Plugin
*************************

Molecule Openstack is designed to allow use of Openstack
for provisioning of test resources.

.. _quickstart:

Quickstart
==========

Installation
------------

.. code-block:: bash

    pip install molecule-plugins

Create a scenario
-----------------

In a pre-existing role
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

   molecule init scenario -d openstack

This will create a default scenario with the openstack driver
in a molecule folder, located in the current working directory.

Example
-------
This is a molecule.yml example file

.. code-block:: yaml

   dependency:
     name: galaxy
   driver:
     name: openstack
   platforms:
     - name: ubuntu2004
       flavor: m1.small
       image: Ubuntu_22.04
       user: ubuntu
   provisioner:
   name: ansible

Then run

.. code-block:: bash

   molecule test

.. note::
   You need to configure `openstack authentication <https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html#config-environment-variables>` using config file or environment variables.

Documentation
=============

Details on the parameters for the platforms section are detailed in
`<platforms.rst>`__.

.. _license:

License
=======

The `MIT`_ License.

.. _`MIT`: https://github.com/ansible/molecule/blob/master/LICENSE

The logo is licensed under the `Creative Commons NoDerivatives 4.0 License`_.

If you have some other use in mind, contact us.

.. _`Creative Commons NoDerivatives 4.0 License`: https://creativecommons.org/licenses/by-nd/4.0/
