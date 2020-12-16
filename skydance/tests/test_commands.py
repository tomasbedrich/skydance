# Following test cases are based on real communication with controller.

import pytest

from skydance.commands import *


def test_ping():
    assert PingCommand().bytes == bytes.fromhex("800080e18000000100790000")


@pytest.mark.parametrize(
    "zone",
    [256, -1, 99999999999, "foo", None],
)
def test_zone_invalid(zone):
    with pytest.raises(expected_exception=ValueError):
        ZoneCommand.validate_zone(zone)


def test_power_on():
    assert PowerOnCommand(zone=2).bytes == bytes.fromhex("800080e180000002000a010001")


def test_power_off():
    assert PowerOffCommand(zone=2).bytes == bytes.fromhex("800080e180000002000a010000")


def test_master_power_on():
    assert MasterPowerOnCommand().bytes == bytes.fromhex(
        "800080e18000000fff0b0300030001"
    )


def test_master_power_off():
    assert MasterPowerOffCommand().bytes == bytes.fromhex(
        "800080e18000000fff0b0300000000"
    )


def test_brightness_min():
    assert BrightnessCommand(zone=2, brightness=1).bytes == bytes.fromhex(
        "800080e180000002000702000001"
    )


def test_brightness_max():
    assert BrightnessCommand(zone=2, brightness=255).bytes == bytes.fromhex(
        "800080e1800000020007020000ff"
    )


@pytest.mark.parametrize(
    "brightness",
    [0, 256, -1, 99999999999, "foo", None],  # level 0 is invalid!
)
def test_brightness_invalid(brightness):
    with pytest.raises(expected_exception=ValueError):
        BrightnessCommand.validate_brightness(brightness)


def test_temperature_min():
    assert TemperatureCommand(zone=2, temperature=0).bytes == bytes.fromhex(
        "800080e180000002000d02000000"
    )


def test_temperature_max():
    assert TemperatureCommand(zone=2, temperature=255).bytes == bytes.fromhex(
        "800080e180000002000d020000ff"
    )


@pytest.mark.parametrize(
    "temperature",
    [256, -1, 99999999999, "foo", None],
)
def test_temperature_invalid(temperature):
    with pytest.raises(expected_exception=ValueError):
        TemperatureCommand.validate_temperature(temperature)


def test_get_number_of_zones():
    assert GetNumberOfZonesCommand().bytes == bytes.fromhex("800080e18000000100790000")


@pytest.mark.parametrize(
    "response, num",
    [
        (bytes.fromhex("800080e18026510100f910008182838485868788898a8b8c8d8e8f90"), 16),
        (bytes.fromhex("800080e18026510100f9100081828384858687880000000000000000"), 8),
        (bytes.fromhex("800080e18026510100f9100000000000000000000000000000000000"), 0),
    ],
)
def test_get_number_of_zones_response(response, num):
    assert GetNumberOfZonesResponse(response).number == num


@pytest.mark.parametrize(
    "zone",
    range(1, 17),
)
def test_get_zone_name(zone: int):
    res = GetZoneNameCommand(zone=zone).bytes
    zone_encoded = 2 ** (zone - 1)
    expected = bytes().join(
        (
            bytes().fromhex("80 00 80 e1 80 00 00"),
            struct.pack("<H", zone_encoded),
            bytes().fromhex("78 00 00"),
        )
    )
    assert res == expected


@pytest.mark.parametrize(
    "zone",
    [17, 256, 0, -1, 99999999999, "foo", None],
)
def test_get_zone_name_invalid(zone: int):
    with pytest.raises(expected_exception=ValueError):
        GetZoneNameCommand.validate_zone(zone)


@pytest.mark.parametrize(
    "variant",
    [
        bytes.fromhex("800080e18026514000f8100051005a6f6e65205247422b4343540000"),
        bytes.fromhex("800080e18026514000f8100051005a6f6e65205247422b4343542000"),
        bytes.fromhex("800080e18026514000f8100051005a6f6e65205247422b4343542020"),
    ],
)
def test_get_zone_name_response(variant):
    assert GetZoneNameResponse(variant).name == "Zone RGB+CCT"
