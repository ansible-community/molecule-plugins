"""Containers Driver Module."""

import inspect
import os
import shutil

from molecule import logger

_logger = logger.get_logger(__name__)

# Preference logic for picking backend driver to be used.
drivers = os.environ.get("MOLECULE_CONTAINERS_BACKEND", "podman,docker").split(",")
for driver in drivers:
    if shutil.which(driver):
        break
else:
    driver = drivers[0]

# Logic for picking backend is subject to change.
if driver == "docker":
    from molecule_plugins.docker.driver import Docker as DriverBackend
elif driver == "podman":
    from molecule_plugins.podman.driver import Podman as DriverBackend
else:
    raise NotImplementedError(f"Driver {driver} is not supported.")
_logger.debug("Containers driver will use %s backend", driver)


class Container(DriverBackend):
    """
    Container Driver Class.

    This class aims to provide an agnostic container enginer implementation,
    which should allow users to consume whichever enginer they have available.
    """

    def __init__(self, config=None) -> None:
        """Construct Container."""
        super().__init__(config)
        self._name = "containers"
        # Assure that _path points to the driver we would be using, or
        # molecule will fail to find the embedded playbooks.
        self._path = os.path.abspath(os.path.dirname(inspect.getfile(DriverBackend)))

    @property
    def required_collections(self) -> dict[str, str]:
        """Return collections dict containing names and versions required."""
        return {
            "ansible.posix": "1.3.0",
            "community.docker": "1.9.1",
            "containers.podman": "1.8.1",
        }
