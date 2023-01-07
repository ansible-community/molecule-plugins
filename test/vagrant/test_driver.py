from molecule import api


def test_driver_is_detected():
    assert "vagrant" in [str(d) for d in api.drivers()]
