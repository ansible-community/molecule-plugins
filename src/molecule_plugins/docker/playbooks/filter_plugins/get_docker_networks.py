"""Embedded ansible filter used by Molecule Docker driver create playbook."""


def get_docker_networks(data, labels={}):
    """Get list of docker networks."""
    network_list = []
    network_names = []
    for platform in data:
        if "docker_networks" in platform:
            for docker_network in platform["docker_networks"]:
                if "labels" not in docker_network:
                    docker_network["labels"] = {}
                for key in labels:
                    docker_network["labels"][key] = labels[key]

                if "name" in docker_network:
                    network_list.append(docker_network)
                    network_names.append(docker_network["name"])

        # If a network name is defined for a platform but is not defined in
        # docker_networks, add it to the network list.
        if "networks" in platform:
            for network in platform["networks"]:
                if "name" in network:
                    name = network["name"]
                    if name not in network_names:
                        network_list.append({"name": name, "labels": labels})
    return network_list


class FilterModule:
    """Core Molecule filter plugins."""

    def filters(self):
        return {
            "molecule_get_docker_networks": get_docker_networks,
        }
