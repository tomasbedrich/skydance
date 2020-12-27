from collections import deque
from typing import Sequence


# TODO is this reimplementing https://docs.python.org/3/library/asyncio-protocol.html#asyncio.BufferedProtocol.buffer_updated ?


class Buffer:
    """
    A buffer which allows feeding chunks of messages and reading them out complete.

    It is specificaly tailored for:

    - Protocols sending byte messages ending with pre-defined tail sequence.
    - Tail sequence length must be 2 bytes.
    """

    _TAIL: bytes
    _TAIL_SEQ: Sequence[int]
    _buffer: deque
    _buffered_messages: int

    def __init__(self, tail: bytes):
        """
        Create a Buffer.

        Args:
            tail: Tail byte sequence.
        """
        if len(tail) != 2:
            raise ValueError(
                "This buffer class supports only protocols with `len(tail) == 2`."
            )
        self._TAIL = tail
        self._TAIL_SEQ = tuple(tail)  # this is handy for implementation
        self._buffer = deque()
        self._buffered_messages = 0

    def reset(self):
        """Clear state without a need to create a new one."""
        self._buffer.clear()
        self._buffered_messages = 0

    @property
    def is_message_ready(self):
        """Return whether at least one message is ready to read."""
        return self._buffered_messages > 0

    def feed(self, chunk: bytes):
        """
        Feed byte chunk into a buffer.

        Update count of messages contained in the buffer.

        Args:
            chunk: Byte chunk of any length.
        """
        previous_tail_byte = self._buffer[-1] if self._buffer else None
        self._buffer.extend(chunk)

        # detect TAIL occurence on the boundary of two chunks
        if previous_tail_byte is not None and chunk:
            last_word = previous_tail_byte, chunk[0]
            if last_word == self._TAIL_SEQ:
                self._buffered_messages += 1

        self._buffered_messages += chunk.count(self._TAIL)

    def get_message(self) -> bytes:
        """
        Return a single message.

        Raise:
            ValueError: If message is incomplete.
        """
        if not self.is_message_ready:
            raise ValueError("No complete message is buffered yet.")

        res = []
        last_byte, byte = None, None
        while True:
            last_byte, byte = byte, self._buffer.popleft()
            res.append(byte)
            if last_byte is not None:
                last_word = last_byte, byte
                if last_word == self._TAIL_SEQ:
                    self._buffered_messages -= 1
                    break
        return bytes(res)
