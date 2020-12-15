# Following test cases are based on real communication with controller.

import pytest

from skydance.commands import *


def test_ping():
    assert bytes.fromhex("800080e18000000100790000") == PingCommand().bytes


@pytest.mark.parametrize(
    "zone",
    [256, -1, 99999999999, "foo", None],
)
def test_zone_invalid(zone):
    with pytest.raises(expected_exception=ValueError):
        ZoneCommand.validate_zone(zone)


def test_power_on():
    assert bytes.fromhex("800080e180000002000a010001") == PowerOnCommand(zone=2).bytes


def test_power_off():
    assert bytes.fromhex("800080e180000002000a010000") == PowerOffCommand(zone=2).bytes


def test_master_power_on():
    assert bytes.fromhex("800080e18000000fff0b0300030001") == MasterPowerOnCommand().bytes


def test_master_power_off():
    assert bytes.fromhex("800080e18000000fff0b0300000000") == MasterPowerOffCommand().bytes


def test_brightness_min():
    assert (
        bytes.fromhex("800080e180000002000702000001")
        == BrightnessCommand(zone=2, brightness=1).bytes
    )


def test_brightness_max():
    assert (
        bytes.fromhex("800080e1800000020007020000ff")
        == BrightnessCommand(zone=2, brightness=255).bytes
    )


@pytest.mark.parametrize(
    "brightness",
    [0, 256, -1, 99999999999, "foo", None],  # level 0 is invalid!
)
def test_brightness_invalid(brightness):
    with pytest.raises(expected_exception=ValueError):
        BrightnessCommand.validate_brightness(brightness)


def test_temperature_min():
    assert (
        bytes.fromhex("800080e180000002000d02000000")
        == TemperatureCommand(zone=2, temperature=0).bytes
    )


def test_temperature_max():
    assert (
        bytes.fromhex("800080e180000002000d020000ff")
        == TemperatureCommand(zone=2, temperature=255).bytes
    )


@pytest.mark.parametrize(
    "temperature",
    [256, -1, 99999999999, "foo", None],
)
def test_temperature_invalid(temperature):
    with pytest.raises(expected_exception=ValueError):
        TemperatureCommand.validate_temperature(temperature)
