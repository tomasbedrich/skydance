# Following test cases are based on real communication with controller.

# pylint: disable=redefined-outer-name

import asyncio
import pytest
from unittest.mock import Mock

from skydance.controller import Controller


@pytest.fixture
def controller():
    reader, writer = Mock(asyncio.StreamReader), Mock(asyncio.StreamWriter)
    return Controller(reader, writer)


@pytest.mark.asyncio
async def test_ping(controller):
    await controller.ping()
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e18000000100790000007e")
    )


@pytest.mark.asyncio
async def test_power_on_zone(controller):
    await controller.power_zone(2, True)
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e180000002000a010001007e")
    )


@pytest.mark.asyncio
async def test_power_off_zone(controller):
    await controller.power_zone(2, False)
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e180000002000a010000007e")
    )


# TODO rewrite to test validators itself + one example validator integration test
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "zone, state",
    {
        # invalid zones
        (256, 100),
        (-1, 100),
        (99999999999, 100),
        ("foo", 100),
        (None, 100),
    },
)
async def test_power_zone_invalid(controller, zone, state):
    with pytest.raises(expected_exception=ValueError):
        await controller.power_zone(zone, state)


@pytest.mark.asyncio
async def test_dim_zone_min(controller):
    await controller.dim_zone(2, 1)
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e180000002000702000001007e")
    )


@pytest.mark.asyncio
async def test_dim_zone_max(controller):
    await controller.dim_zone(2, 255)
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e1800000020007020000ff007e")
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "zone, level",
    {
        # invalid levels
        (2, 0),  # level 0 is invalid!
        (2, 256),
        (2, -1),
        (2, 99999999999),
        (2, "foo"),
        (2, None),
        # invalid zones
        (256, 100),
        (-1, 100),
        (99999999999, 100),
        ("foo", 100),
        (None, 100),
    },
)
async def test_dim_zone_invalid(controller, zone, level):
    with pytest.raises(expected_exception=ValueError):
        await controller.dim_zone(zone, level)


@pytest.mark.asyncio
async def test_temp_zone_min(controller):
    await controller.temp_zone(2, 0)
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e180000002000d02000000007e")
    )


@pytest.mark.asyncio
async def test_temp_zone_max(controller):
    await controller.temp_zone(2, 255)
    controller.writer.write.assert_called_once_with(
        bytes.fromhex("55aa5aa57e00800080e180000002000d020000ff007e")
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "zone, level",
    {
        # invalid levels
        (2, 256),
        (2, -1),
        (2, 99999999999),
        (2, "foo"),
        (2, None),
        # invalid zones
        (256, 100),
        (-1, 100),
        (99999999999, 100),
        ("foo", 100),
        (None, 100),
    },
)
async def test_temp_zone_invalid(controller, zone, level):
    with pytest.raises(expected_exception=ValueError):
        await controller.temp_zone(zone, level)
