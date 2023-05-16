*********************
Options documentation
*********************

Authentication
==============

See https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html#config-environment-variables

Platform Arguments
==================

=============================== ===============================================
  Variable                        Description
=============================== ===============================================
description                     Set description for instance, \
                                default = 'Molecule test instance'
flavor                          Set flavor for instance
image                           Set instance image
security_group                  Mapping of security_group settings (optional)
security_group.name             Name of security_group
security_group.create           Create security group, default = true
security_group.description      Description of security_group
security_group.rules            Ingress Rules (list) defined in security_group
security_group.rules[].proto    Protocol for rule
security_group.rules[].port     Port
security_group.rules[].cidr     Source IP address(es) in CIDR notation
security_group.rules[].port_min Starting port (can't be used with port)
security_group.rules[].port_max Ending port (can't be used with port)
security_group.rules[].type     IPv4 or IPv6, default 'IPv4'
user                            Default user of image
=============================== ===============================================


Image User
==========

More information: https://docs.openstack.org/image-guide/obtain-images.html

Security Groups
===============

If you specifiy a security group,
the security group will be managed by create and destroy playbook.
You can define some rules (see example below).

You can use unmanaged security groups by specifying the name of the group
and setting `create` to `false` (see debian11 example below).
In this case, the specified security group must exist.

Examples
========

.. code-block:: yaml

    platforms:
      - name: debian10
        flavor: m1.small
        image: Debian_10
        user: debian
        security_group:
          name: molecule
          description: Molecule test
          rules:
            - proto: tcp
              port: 22
              cidr: 0.0.0.0/0
            - proto: tcp
              port: 22
              cidr: '::/0'
              type: IPv6
            - proto: icmp
              port: -1
              cidr: 0.0.0.0/0
            - proto: tcp
              port_min: 5000
              port_max: 5050
              cidr: 0.0.0.0/0
      - name: debian11
        flavor: m1.small
        image: Debian_11
        user: debian
        security_group:
          name: existing-sec
          create: false
