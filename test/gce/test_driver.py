from molecule import api


def test_driver_is_detected():
    driver_name = __name__.split(".")[0].split("_")[-1]
    drivers = [str(d) for d in api.drivers()]
    assert driver_name in drivers
