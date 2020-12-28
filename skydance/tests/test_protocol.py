import pytest

from skydance.protocol import *


@pytest.fixture(name="state")
def state_fixture():
    return State()


def test_state_frame_number_overflow():
    s = State()
    for _ in range(256):
        s.increment_frame_number()
    assert s.frame_number == bytes([0])


def test_command_bytes(state):
    assert PingCommand(state).raw == bytes.fromhex(
        "55aa5aa57e00800080e18000000100790000007e"
    )


def test_ping(state):
    assert PingCommand(state).body == bytes.fromhex("800080e18000000100790000")


@pytest.mark.parametrize(
    "zone",
    [256, -1, 99999999999, "foo", None],
)
def test_zone_invalid(zone):
    with pytest.raises(expected_exception=ValueError):
        ZoneCommand.validate_zone(zone)


def test_power_on(state):
    assert PowerOnCommand(state, zone=2).body == bytes.fromhex(
        "800080e180000002000a010001"
    )


def test_power_on_higher_zone_number(state):
    assert PowerOnCommand(state, zone=15).body == bytes.fromhex(
        "800080e180000000400a010001"
    )


def test_power_off(state):
    assert PowerOffCommand(state, zone=2).body == bytes.fromhex(
        "800080e180000002000a010000"
    )


def test_master_power_on(state):
    assert MasterPowerOnCommand(state).body == bytes.fromhex(
        "800080e18000000fff0b0300030001"
    )


def test_master_power_off(state):
    assert MasterPowerOffCommand(state).body == bytes.fromhex(
        "800080e18000000fff0b0300000000"
    )


def test_brightness_min(state):
    assert BrightnessCommand(state, zone=2, brightness=1).body == bytes.fromhex(
        "800080e180000002000702000001"
    )


def test_brightness_max(state):
    assert BrightnessCommand(state, zone=2, brightness=255).body == bytes.fromhex(
        "800080e1800000020007020000ff"
    )


@pytest.mark.parametrize(
    "brightness",
    [0, 256, -1, 99999999999, "foo", None],  # level 0 is invalid!
)
def test_brightness_invalid(brightness):
    with pytest.raises(expected_exception=ValueError):
        BrightnessCommand.validate_brightness(brightness)


def test_temperature_min(state):
    assert TemperatureCommand(state, zone=2, temperature=0).body == bytes.fromhex(
        "800080e180000002000d02000000"
    )


def test_temperature_max(state):
    assert TemperatureCommand(state, zone=2, temperature=255).body == bytes.fromhex(
        "800080e180000002000d020000ff"
    )


@pytest.mark.parametrize(
    "temperature",
    [256, -1, 99999999999, "foo", None],
)
def test_temperature_invalid(temperature):
    with pytest.raises(expected_exception=ValueError):
        TemperatureCommand.validate_temperature(temperature)


def test_get_number_of_zones(state):
    assert GetNumberOfZonesCommand(state).body == bytes.fromhex(
        "800080e18000000100790000"
    )


number_of_zones_params = {
    "55aa5aa57e00800080e18026510100f910008182838485868788898a8b8c8d8e8f90007e": 16,
    "55aa5aa57e00800080e18026510100f9100081828384858687880000000000000000007e": 8,
    "55aa5aa57e00800080e18026510100f9100000000000000000000000000000000000007e": 0,
}


@pytest.mark.parametrize(
    "response, num",
    [(bytes.fromhex(res), num) for res, num in number_of_zones_params.items()],
)
def test_get_number_of_zones_response(response, num):
    assert GetNumberOfZonesResponse(response).number == num


@pytest.mark.parametrize(
    "zone",
    range(1, 17),
)
def test_get_zone_name(state, zone: int):
    res = GetZoneNameCommand(state, zone=zone).body
    zone_encoded = 2 ** (zone - 1)
    expected = bytes().join(
        (
            bytes.fromhex("80 00 80 e1 80 00 00"),
            struct.pack("<H", zone_encoded),
            bytes.fromhex("78 00 00"),
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
        bytes.fromhex(
            "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343540000007e"
        ),
        bytes.fromhex(
            "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343542000007e"
        ),
        bytes.fromhex(
            "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343542020007e"
        ),
    ],
)
def test_get_zone_name_response_strip(variant):
    assert GetZoneNameResponse(variant).name == "Zone RGB+CCT"


def test_get_zone_name_response_utf_8():
    raw = bytes.fromhex(
        "55aa5aa57e02800080e18026510200f8100021004b75636879c58820746f70000000007e"
    )
    assert GetZoneNameResponse(raw).name == "Kuchyň top"
