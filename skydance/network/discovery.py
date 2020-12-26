import asyncio
import ipaddress
import logging
import socket
from typing import Optional, Union, cast


log = logging.getLogger(__name__)


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """
    Implement discovery protocol used by Skydance lighting WiFi relay.

    Skydance uses HF-LPT130 chip for network communication (WiFi settings,
    passing network data to another chips inside, network discovery).

    Example usage:
    >>> loop = asyncio.get_event_loop()
    >>> protocol = DiscoveryProtocol("192.168.1.255", broadcast=True)
    >>> await loop.create_datagram_endpoint(lambda: protocol, family=socket.AF_INET)
    >>> for _ in range(3):
    >>>     protocol.send_discovery_request()
    >>>     await asyncio.sleep(1)
    >>> print(protocol.result)

    See:
    - http://www.hi-flying.com/hf-lpt130
    - https://github.com/zoot1612/plugin_mh/blob/master/MH_Control
    """

    DISCOVERY_REQUEST = b"HF-A11ASSISTHREAD"
    PORT = 48899

    transport: Optional[asyncio.transports.DatagramTransport] = None
    ip: ipaddress.IPv4Address
    broadcast: bool
    result: dict

    def __init__(
        self, ip: Union[str, ipaddress.IPv4Address], *, broadcast: bool = True
    ):
        self.ip = ipaddress.IPv4Address(ip)
        self.broadcast = broadcast
        self.result = dict()

    def connection_made(self, transport):
        log.debug(
            "Starting discovery protocol, broadcast=%s",
            "on" if self.broadcast else "off",
        )
        self.transport = cast(asyncio.transports.DatagramTransport, transport)
        if self.broadcast:
            sock: socket.socket = transport.get_extra_info("socket")
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def datagram_received(self, data: bytes, addr):
        real_ip_str, _port = addr
        log.debug("Discovery reply received from %s: %s", real_ip_str, data)
        _reported_ip_str, mac_str, _model = data.decode("ascii").split(",")
        real_ip = ipaddress.IPv4Address(real_ip_str)
        mac = bytes.fromhex(mac_str)
        self.result[mac] = real_ip

    def send_discovery_request(self):
        if not self.transport:
            raise ValueError(
                "Transport is not available. "
                "The protocol must be first initiated using `create_datagram_endpoint`."
            )
        log.debug("Sending discovery request to %s", self.ip)
        self.transport.sendto(self.DISCOVERY_REQUEST, (str(self.ip), self.PORT))
