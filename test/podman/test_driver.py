"""Unit tests."""

from molecule import api
from molecule_plugins.podman.driver import Podman


def test_podman_driver_is_detected():
    """Asserts that molecule recognizes the driver."""
    assert any(str(d) == "podman" for d in api.drivers())


def test_driver_initializes_without_podman_executable(monkeypatch):
    """Make sure we can initiaize driver without having an executable present."""
    monkeypatch.setenv("MOLECULE_PODMAN_EXECUTABLE", "bad-executable")
    Podman()
