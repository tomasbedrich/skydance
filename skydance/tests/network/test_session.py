import pytest
from unittest.mock import AsyncMock, Mock, patch

from skydance.network.session import Session


@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_read_fail(open_connection_mock):
    """Simulate simple read failure."""
    fake_reader, fake_writer = AsyncMock(), AsyncMock()
    open_connection_mock.return_value = fake_reader, fake_writer
    fake_reader.read = AsyncMock(
        side_effect=[ConnectionResetError(), ConnectionAbortedError(), bytes([1, 2, 3])]
    )
    fake_writer.close = Mock()
    async with Session("127.0.0.1", 123) as session:
        res = await session.read()
        assert fake_reader.read.call_count == 3
        assert res == bytes([1, 2, 3])


@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_write_fail(open_connection_mock):
    """Simulate simple write failure."""
    fake_reader, fake_writer = AsyncMock(), AsyncMock()
    open_connection_mock.return_value = fake_reader, fake_writer
    fake_writer.write = Mock(
        side_effect=[ConnectionResetError(), ConnectionAbortedError(), None]
    )
    fake_writer.close = Mock()
    async with Session("127.0.0.1", 123) as session:
        await session.write(bytes([0]))
        assert fake_writer.write.call_count == 3
        assert fake_writer.drain.call_count == 1


@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_drain_and_wait_closed_fail(open_connection_mock):
    """
    Simulate complex connection failure.

    Fail during writer.drain() + simulate damaged pipe during connection closing.
    """
    fake_reader, fake_writer = AsyncMock(), AsyncMock()
    open_connection_mock.return_value = fake_reader, fake_writer
    fake_writer.write = Mock()
    fake_writer.drain = AsyncMock(side_effect=[ConnectionResetError(), None])
    fake_writer.close = Mock()
    fake_writer.wait_closed = AsyncMock(
        side_effect=[BrokenPipeError(), TimeoutError(), None]
    )
    async with Session("127.0.0.1", 123) as session:
        await session.write(bytes([0]))
        assert fake_writer.write.call_count == 2
        assert fake_writer.drain.call_count == 2
        assert fake_writer.close.call_count == 1
        assert fake_writer.wait_closed.call_count == 1


@pytest.mark.asyncio
async def test_close_unopened():
    s = Session("127.0.0.1", 123)
    await s.close()
