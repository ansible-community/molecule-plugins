*******************
Molecule EC2 Plugin
*******************

.. image:: https://badge.fury.io/py/molecule-ec2.svg
   :target: https://badge.fury.io/py/molecule-ec2
   :alt: PyPI Package

.. image:: https://zuul-ci.org/gated.svg
   :target: https://dashboard.zuul.ansible.com/t/ansible/builds?project=ansible-community/molecule-ec2

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

Molecule EC2 is designed to allow use of AWS EC2 for provisioning of test
resources.

.. _quickstart:

Quickstart
==========

Installation
------------
.. code-block:: bash

   pip install molecule-ec2

Create a scenario
-----------------

With a new role
^^^^^^^^^^^^^^^
.. code-block:: bash

   molecule init role -d ec2 my-role

This will create a new folder *my-role* containing a bare-bone generated
role like you would do with ``ansible-galaxy init`` command.
It will also contain a molecule folder with a default scenario
using the ec2 driver (using ansible community.aws.ec2_instance collection).
Install the collection using
`ansible-galaxy install -r test_requirements.yml`.

In a pre-existing role
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

   molecule init scenario -d ec2

This will create a default scenario with the ec2 driver in a molecule folder,
located in the current working directory.

Example
-------
This is a molecule.yml example file

.. code-block:: yaml

   dependency:
      name: galaxy
   driver:
      name: ec2
   platforms:
     - name: instance
       image_owner: "099720109477"
       image_name: ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*
       instance_type: t2.micro
       vpc_subnet_id: <your-aws-vpc-subnet-id>
       tags:
         Name: molecule_instance
   provisioner:
     name: ansible
   verifier:
     name: ansible

All you need to do is fill in the subnet-id you want
to create your test instance into.
Then run

.. code-block:: bash

   molecule test

.. note::
   To make this work, you need to export your AWS credentials, as well as the AWS region you want to use, in your environment.

   .. code-block:: bash

      export AWS_ACCESS_KEY_ID=ACCESS_API_KEY
      export AWS_SECRET_KEY=SECRET_API_KEY
      export AWS_REGION=us-east-1

   You can read more about managing AWS credentials with Ansible modules
   in the official documentation of the `Ansible AWS modules <https://docs.ansible.com/ansible/latest/collections/amazon/aws>`_

Documentation
=============

Details on the parameters for the platforms section are detailed in
`<platforms.rst>`__.

Read the molecule documentation and more at https://molecule.readthedocs.io/.

.. _get-involved:

Get Involved
============

* Join us in the ``#ansible-molecule`` channel on `Freenode`_.
* Join the discussion in `molecule-users Forum`_.
* Join the community working group by checking the `wiki`_.
* Want to know about releases, subscribe to `ansible-announce list`_.
* For the full list of Ansible email Lists, IRC channels see the
  `communication page`_.

.. _`Freenode`: https://freenode.net
.. _`molecule-users Forum`: https://groups.google.com/forum/#!forum/molecule-users
.. _`wiki`: https://github.com/ansible/community/wiki/Molecule
.. _`ansible-announce list`: https://groups.google.com/group/ansible-announce
.. _`communication page`: https://docs.ansible.com/ansible/latest/community/communication.html

.. _authors:

Authors
=======

Molecule EC2 Plugin was created by Sorin Sbarnea based on code from
Molecule.

.. _license:

License
=======

The `MIT`_ License.

.. _`MIT`: https://github.com/ansible/molecule/blob/master/LICENSE

The logo is licensed under the `Creative Commons NoDerivatives 4.0 License`_.

If you have some other use in mind, contact us.

.. _`Creative Commons NoDerivatives 4.0 License`: https://creativecommons.org/licenses/by-nd/4.0/
