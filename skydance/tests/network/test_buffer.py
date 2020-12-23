import pytest

from skydance.network.buffer import Buffer


def test_init():
    Buffer(bytes([0, 0]))


@pytest.mark.parametrize(
    "tail",
    [(), (0,), (0, 0, 0)],
)
def test_invalid_tail(tail):
    with pytest.raises(expected_exception=ValueError):
        Buffer(bytes(tail))


def test_feed():
    buffer = Buffer(bytes([0, 0]))
    assert not buffer.is_message_ready
    buffer.feed(bytes([1, 2, 3, 0, 0]))
    assert buffer.is_message_ready
    assert buffer.get_message() == bytes([1, 2, 3, 0, 0])


def test_feed_shorter_than_tail():
    buffer = Buffer(bytes([0, 0]))
    buffer.feed(bytes([1]))
    buffer.feed(bytes([2]))
    buffer.feed(bytes([3]))
    buffer.feed(bytes([0]))
    assert not buffer.is_message_ready
    buffer.feed(bytes([0]))
    assert buffer.is_message_ready
    assert buffer.get_message() == bytes([1, 2, 3, 0, 0])


def test_feed_tail_together():
    buffer = Buffer(bytes([0, 0]))
    buffer.feed(bytes([1, 2, 3]))
    assert not buffer.is_message_ready
    buffer.feed(bytes([0, 0]))
    assert buffer.is_message_ready
    assert buffer.get_message() == bytes([1, 2, 3, 0, 0])


def test_feed_tail_split():
    buffer = Buffer(bytes([0, 0]))
    buffer.feed(bytes([1, 2, 3, 0]))
    assert not buffer.is_message_ready
    buffer.feed(bytes([0]))
    assert buffer.is_message_ready
    assert buffer.get_message() == bytes([1, 2, 3, 0, 0])


def test_feed_get_message_incomplete():
    buffer = Buffer(bytes([0, 0]))
    buffer.feed(bytes([1, 2, 3, 0]))
    with pytest.raises(expected_exception=ValueError):
        assert buffer.get_message()


def test_reset():
    buffer = Buffer(bytes([0, 0]))
    buffer.feed(bytes([5, 5, 5]))
    buffer.reset()
    buffer.feed(bytes([1, 2, 3, 0, 0]))
    assert buffer.get_message() == bytes([1, 2, 3, 0, 0])
