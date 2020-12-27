import pytest

from skydance.network.discovery import DiscoveryProtocol


def test_misuse():
    protocol = DiscoveryProtocol()
    with pytest.raises(expected_exception=ValueError):
        protocol.send_discovery_request()
