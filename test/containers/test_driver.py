"""Unit Tests."""
from molecule import api


def test_driver_is_detected():
    """Check that driver is recognized."""
    assert "containers" in [str(d) for d in api.drivers()]
