import pytest

from skydance.session import Session


# TODO test reading

# TODO test writing


@pytest.mark.asyncio
async def test_close_unopened():
    s = Session("127.0.0.1")
    await s.close()
