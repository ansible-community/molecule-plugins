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
network                         Mapping of network settings (optional)
network.name                    Name of network
network.create                  Create network, default = true
network.router                  Mapping of network router settings
network.router.name             Name of router
network.router.ext_network      External gateway network
network.router.snat             Enable or disable snat, default = omit
network.subnet                  Mapping of network subnet settings
network.subnet.name             Name of subnet
network.subnet.cidr             CIDR of subnet
network.subnet.ipv              IP Version, default = 4
network.subnet.dns_nameservers  List of dns nameservers, default = omit
network.subnet.host_routers     List of host router (destination, nexthop), \
                                default = omit
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
volume                          Mapping of volume settings (optional if \
                                flavor provides volume)
volume.size                     Size of volume (GB)
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

Networks
========

If you specify a network,
the network will be managed by create and destroy playbook.
You need to define a subnet and router (see example below).

You can use unmanaged network by specifying the name of the network
and setting `create` to `false`.
In this case, the specified network must exist.


Volumes
=======

If you specify a volume,
the volume will be managed by create and destroy playbook.
You need to define the size of the volume.

This setting is required if your flavor doesn't provide a disk.

Examples
========

.. code-block:: yaml

    platforms:
      - name: debian10
        flavor: m1.small
        image: Debian_10
        user: debian
        network:
          name: molecule
          router:
            name: router1
            ext_network: public
            subnet: subnet1
          subnet:
            name: subnet1
            cidr: 192.168.11.0/24
            ipv: 4 # default
            dns_nameservers: # default omit
              - 8.8.8.8
            host_routes: # default omit
              - destination: 192.168.0.0/24
                nexthop: 192.168.0.1
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
        network:
          name: molecule # use network from debian10 instance
      - name: ubuntu2004
        falvor: m1.tiny
        image: Ubuntu_2004
        user: ubuntu
        security_group:
          name: molecule # use security group from debian10 instance
        network:
          name: existing-net # use existing network
          create: false
        volume:
          size: 10 # GB
