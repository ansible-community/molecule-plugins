from molecule import api


def test_driver_is_detected():
    assert "ec2" in [str(d) for d in api.drivers()]
