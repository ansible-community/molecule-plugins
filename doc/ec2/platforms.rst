*********************
Options documentation
*********************

Molecule EC2 allows a wide degree of customisation via platform arguments.

Environment Variables
=====================

In addition to the standard molecule environment variables, the following
system environment variables are used.

=========================== ===================================================
  Variable                    Description
=========================== ===================================================
AWS_PROFILE                 Sets the aws_profile parameter if it is supplied
=========================== ===================================================

Platform Arguments
==================

=========================== ===================================================
  Variable                    Description
=========================== ===================================================
assign_public_ip            Assign a public ip, default = True
aws_profile                 Boto profile, default = AWS_PROFILE or omits
boot_wait_seconds           Amount of time to wait after ssh starts
cloud_config                Dictionary suitable for instance user_data
connection_options          See Connection Options section
image                       AMI to use, see Image Selection section
image_filters               Filters to select AMI, see Image Selection section
image_name                  Name of AMI, see Image Selection section
image_owner                 Owner of AMI, see Image Selection section
instance_type               AWS EC2 instance type, defaults to t3a.medium
key_inject_method           "cloud-init" or "ec2", see SSH Key section
key_name                    SSH key name, see SSH Key section
name                        Name for platform entry, used for Ansible inventory
private_key_path            SSH key private path, see SSH Key section
public_key_path             Not used
region                      AWS region to use, defaults to AWS boto defaults
security_group_name         Name group to create, see Security Group section
security_group_description  Group description, see Security Group section
security_group_rules        Group ingress rules, see Security Group section
security_group_rules_egress Group egress rules, see Security Group section
security_groups             List of security groups, see Security Group section
ssh_user                    SSH user to use, defaults to ubuntu, \
                            see SSH Key section
ssh_port                    SSH port to use
tags                        Map of tags to apply to the instance
volumes                     List of volumes as per aws.ec2_instance_module
vpc_filters                 Filters to select VPC, see VPC Selection section
vpc_id                      VPC ID, see VPC Selection section
vpc_subnet_filters          Filters to select Subnet,\
                            see Subnet Selection section
vpc_subnet_id               Subnet ID, see Subnet Selection section
=========================== ===================================================

Image Selection
===============

The platform must specify an AMI for the image to use.

This can be done directly, by setting the `image` parameter.

Or it can be done indirectly, causing an AMI to be discovered using the
`awazon.aws.ec2_ami_info` command.

When using an indirect search, the `aws_profile` and `region` option will be
used.
The `image_owner` option will be used to select by owner if provided.
The `image_name` option will be used to create a filter selecting by name.
The `image_filters` option should be a dict, this will filter by key and value
to select an image.

If both `image_name` and `image_filters` is set, the name filter will be added
to the supplied filters.

When a search returns multiple images the newest creation_date will be used.

Examples
--------

.. code-block:: yaml

   platforms:
     - name: debian10
       image: ami-0f31df35880686b3f
       region: us-east-1
     - name: ubuntu1804
       image_owner: 099720109477  # Ubuntu
       image_name: ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*
     - name: kali
       image_owner: aws-marketplace
       image_filters:
         product-code: 89bab4k3h9x4rkojcm2tj8j4l
     - name: RHEL8
       image_owner: 309956199498  # Redhat
       image_name: RHEL-8*
       image_filters:
         architecture: arm64
         virtualization-type: hvm
       instance_type: t4g.small  # ARM64


SSH Key
=======

There are a variety of options which control the ssh key used for a host.

The first, and most important option is `key_inject_method`.
This can either be `cloud-init` or `ec2`, it defaults to `cloud-init`.

The cloud-init method injects the public key in via the cloud-init user data.
This creates a user, `ssh_user`, adds the public_key and grants passwordless
sudo access.

The ec2 method creates an AWS managed key called `key_name`.
The instance is created and associated with that key, the default cloud-init
setup typically adds this to the default user.
For this configuration the `ssh_user` option is ignored, the user is the
default for the image being used.

For either option the `private_key_path` can be supplied to specify an
existing key.
Otherwise one is generated specifically for the creation.

`public_key_path` is not actually used.

Examples
--------

.. code-block:: yaml

   platforms:
     - name: debian_as_ubuntu
       image: ami-0f31df35880686b3f
       region: us-east-1
       # Login user will be overridden from admin to ubuntu
       # Generated private key will be used
     - name: debian_as_admin
       image: ami-0f31df35880686b3f
       region: us-east-1
       key_inject_method: ec2
       connection_options:
         ansible_user: admin  # default debian cloud user
     - name: debian_my_key
       image: ami-0f31df35880686b3f
       region: us-east-1
       key_inject_method: ec2
       key_name: my-key
       private_key_path: ~/.ssh/id_rsa
       # Existing private key will be used


Security Group
==============

Molecule EC2 can either use an existing security group or create one for the
test.

To use an existing security group the option `security_groups` should be a list
of of existing security groups.

If one or more existing groups are not specified one will be created, this is
performed using the `amazon.aws.ec2_group` plugin.

The `security_group_name`, `security_group_description`,
`security_group_rules`, and `security_group_rules_egress` options are passed
directly to `ec2_group` and are as documented there.

The created security group will allow incoming ssh traffic and ICMP, all
outgoing traffic will be permitted.

Note that specifying `security_group_name` will cause a new security group to
be created in that name, replacing any existing security group.

Examples
--------

.. code-block:: yaml

   platforms:
     - name: debian10
       image: ami-0f31df35880686b3f
       region: us-east-1
       # Default security group will be created in the first VPC
     - name: debian_my_sg
       image: ami-0f31df35880686b3f
       region: us-east-1
       security_groups: [ "public" ]
       # Existing public security group will be used
     - name: debian_specify_sg
       image: ami-0f31df35880686b3f
       region: us-east-1
       security_group_name: mole-whacked
       security_group_description: Wacking harder than we've wacked before
       security_group_rules:
         - proto: all
           group_name: vpn
           rule_desc: only allow access from the VPN
       security_group_rules_egress:
         - proto: tcp
           from_port: 80
           to_port: 80
           cidr_ip: "0.0.0.0/0"
           rule_desc: only allow old school web browsing
         - proto: udp
           from_port: 27015
           to_port: 27030
           cidr_ip:
             - 45.121.184.0/23
             - 45.121.186.0/23
             - 103.10.124.0/24
           cidr_ipv6:
             - 2404:3fc0::/48
             - 2404:3fc0:1:/48
             - 2404:3fc0:4:/47
           rule_desc: allow valve steam subset


VPC Selection
=============

The VPC that the EC2 image will be created in can be specified or chosen
automatically.

It can be specified directly by setting the `vpc_id` option.

It can be specified indirectly by setting the `vpc_subnet_id` option.

It can be selected by using the `vpc_filters` option, this is a dictionary
which will be used by amazon.aws.ec2_vpc_net_info to select a VPC.

If no VPC selection parameters are provided all vpcs will be selected.

When multiple VPCs are selected the first is chosen, the order is not
guaranteed.


Examples
--------

.. code-block:: yaml

   platforms:
     - name: first_vpc
       image: ami-0f31df35880686b3f
       region: us-east-1
     - name: specify_vpc
       image: ami-0f31df35880686b3f
       region: us-east-1
       vpc_id: vpc-3f64b58
     - name: specify_subnet
       image: ami-0f31df35880686b3f
       region: us-east-1
       vpc_subnet_id: subnet-a18bfcc6
     - name: filter_vpc
       image: ami-0f31df35880686b3f
       region: us-east-1
       vpc_filters:
         "tag:Name": Testground


Subnet Selection
================

The subnet that the EC2 image will be created in can be specified or chosen
automatically.

It can be specified directly by setting the `vpc_subnet_id` option.

It can be selected by using the `subnet_filters` option, this is a dictionary
which will be used by amazon.aws.ec2_vpc_subnet_info to select a subnet.

If no selection parameters are provided all subnets will be selected.

If the `vpc_id` option is specified, it will be used to filter to that VPC,
combining with `subnet_filters` if necessary.

When multiple subnets are selected the first is chosen, the order is not
guaranteed.

Examples
--------

.. code-block:: yaml

   platforms:
     - name: first_subnet
       image: ami-0f31df35880686b3f
       region: us-east-1
     - name: first_subnet_in_specified_vpc
       image: ami-0f31df35880686b3f
       region: us-east-1
       vpc_id: vpc-3f64b58
     - name: specify_subnet
       image: ami-0f31df35880686b3f
       region: us-east-1
       vpc_subnet_id: subnet-a18bfcc6
     - name: filter_subnet
       image: ami-0f31df35880686b3f
       region: us-east-1
       subnet_filters:
         availability-zone: us-east-1b

Connection Options
==================

Connection options to pass to the Ansible inventory such as `ansible_user`.

Special handling is performed if the `ansible_connection` option is `winrm`.
If the password is not set via the `ansible_password` option, it will be
retrieved using the AWS boto3 client and set.

The `ansible_connection` option being `winrm` is also used to choose between
`ssh` and `xfreerdp` when using the `molecule login` command.

Examples
--------

.. code-block:: yaml

   platforms:
     - name: debian10
       image: ami-0f31df35880686b3f
       region: us-east-1
       connection_options:
         ansible_user: admin  # default debian cloud user
         ansible_become: true
         ansible_python_interpereter: /usr/bin/python3
     - name: win2016
       image_name: Windows_Server-2016-English-Full-Base-*
       image_owner: amazon
       security_groups: [ "win" ]
       key_inject_method: ec2
       connection_options:
         sudo: false
         ansible_user: Administrator
         ansible_port: 5986
         ansible_connection: winrm
         ansible_winrm_scheme: https
         ansible_winrm_server_cert_validation: ignore
         connection: winrm
