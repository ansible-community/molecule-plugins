from molecule import api


def test_azure_driver_is_detected():
    assert "azure" in [str(d) for d in api.drivers()]
