import pytest
import struct
from unittest.mock import AsyncMock, Mock, patch

from skydance.network.session import Session
from skydance.protocol import HEAD, TAIL, GetNumberOfZonesCommand, PingCommand


def make_reply(frame_number: int, cmd_type: int = 0xF9, payload: bytes = b"\x00" * 16):
    """Build a response frame the same way a relay does."""
    return (
        HEAD
        + bytes([frame_number])
        + bytes.fromhex("800080e180adff0100")  # device type, addresses, zone
        + bytes([cmd_type])
        + struct.pack("<H", len(payload))
        + payload
        + TAIL
    )


def make_session(reader, writer):
    """Create a session with a mocked transport."""
    session = Session("127.0.0.1", 123)
    session.PAUSE_BETWEEN_COMMANDS = 0
    session.COMMAND_TIMEOUT = 0.1
    session._reader = reader
    session._writer = writer
    return session


@pytest.fixture(name="transport")
def transport_fixture():
    reader, writer = AsyncMock(), Mock()
    writer.is_closing = Mock(return_value=False)
    writer.drain = AsyncMock()
    writer.wait_closed = AsyncMock()
    return reader, writer


@pytest.mark.asyncio
async def test_request_returns_reply(transport):
    """A command is written and its reply is returned."""
    reader, writer = transport
    reply = make_reply(0)
    reader.readexactly = AsyncMock(side_effect=[reply[:18], reply[18:]])

    session = make_session(reader, writer)
    result = await session.request(PingCommand)

    assert result == reply
    assert writer.write.call_args[0][0] == bytes.fromhex(
        "55aa5aa57e00800080e18000000100790000007e"
    )


@pytest.mark.asyncio
async def test_frame_number_is_used_up_before_write(transport):
    """Frame numbers do not repeat, even when a request fails."""
    reader, writer = transport
    first_reply, second_reply = make_reply(0), make_reply(1)
    reader.readexactly = AsyncMock(
        side_effect=[
            first_reply[:18],
            first_reply[18:],
            second_reply[:18],
            second_reply[18:],
        ]
    )

    session = make_session(reader, writer)
    await session.request(PingCommand)
    await session.request(PingCommand)

    first, second = (call[0][0] for call in writer.write.call_args_list)
    assert first[len(HEAD)] == 0
    assert second[len(HEAD)] == 1


@pytest.mark.asyncio
async def test_reply_to_another_request_is_skipped(transport):
    """Replies broadcast to other clients are ignored."""
    reader, writer = transport
    foreign, own = make_reply(7), make_reply(0)
    reader.readexactly = AsyncMock(
        side_effect=[
            foreign[:18],
            foreign[18:],
            own[:18],
            own[18:],
        ]
    )

    session = make_session(reader, writer)
    assert await session.request(PingCommand) == own


@pytest.mark.asyncio
async def test_reply_of_another_type_is_skipped(transport):
    """A reply of the same frame number but of another type is ignored."""
    reader, writer = transport
    other_type, own = make_reply(0, cmd_type=0xF8), make_reply(0, cmd_type=0xF9)
    reader.readexactly = AsyncMock(
        side_effect=[
            other_type[:18],
            other_type[18:],
            own[:18],
            own[18:],
        ]
    )

    session = make_session(reader, writer)
    assert await session.request(PingCommand) == own


@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_failed_exchange_reconnects(open_connection_mock, transport):
    """A timed out command is retried once on a fresh connection."""
    reader, writer = transport
    open_connection_mock.return_value = (reader, writer)

    reply = make_reply(1)
    reader.readexactly = AsyncMock(
        side_effect=[
            TimeoutError(),  # first exchange fails
            reply[:18],  # second exchange, frame number is already used up
            reply[18:],
        ]
    )

    session = make_session(reader, writer)
    assert await session.request(PingCommand) == reply
    assert open_connection_mock.await_count == 1
    assert writer.close.call_count == 1


@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_unreachable_relay_fails_fast(open_connection_mock, transport):
    """A failed connect is not retried."""
    _, writer = transport
    open_connection_mock.side_effect = ConnectionRefusedError()

    session = make_session(None, None)
    with pytest.raises(ConnectionRefusedError):
        await session.request(PingCommand)

    assert open_connection_mock.await_count == 1


@pytest.mark.asyncio
async def test_number_of_zones_reply(transport):
    """A real reply is parsed by the library responses."""
    reader, writer = transport
    reply = bytes.fromhex(
        "55aa5aa57e00800080e180adff0100f91000" "0082838405060708090a0b0c0d0e0f10" "007e"
    )
    reader.readexactly = AsyncMock(side_effect=[reply[:18], reply[18:]])

    session = make_session(reader, writer)
    raw = await session.request(GetNumberOfZonesCommand)
    assert raw == reply


@pytest.mark.asyncio
async def test_close_unopened():
    s = Session("127.0.0.1", 123)
    await s.close()
