# molecule-plugins

This repository contains the following molecule plugins:

- azure
- containers
- docker
- ec2
- gce
- openstack
- podman
- vagrant

Installing `molecule-plugins` does not install dependencies specific to each,
plugin. To install these you need to install the extras for each plugin, like
`pip3 install 'molecule-plugins[azure]'`.

Before installing these plugins be sure that you uninstall their old standalone
packages, like `pip3 uninstall molecule-azure`. If you fail to do so, you will
end-up with a broken setup, as multiple plugins will have the same entry points,
registered.
