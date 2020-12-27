import asyncio
import ipaddress
import logging
from collections import defaultdict
from typing import DefaultDict, Iterable, Mapping, Optional, cast


log = logging.getLogger(__name__)

# type aliases
MacAddress = bytes
DiscoveryResult = Mapping[MacAddress, Iterable[ipaddress.IPv4Address]]


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """
    Implement discovery protocol used by Skydance Wi-Fi relays.

    Skydance uses HF-LPT130 chip for network communication (Wi-Fi settings,
    passing network data to another chips inside, network discovery).

    See Also:
    - [HF-LPT130 product page](http://www.hi-flying.com/hf-lpt130)
    - [Similar protocol description](https://github.com/zoot1612/plugin_mh/blob/master/MH_Control)

    Example:
        >>> protocol = DiscoveryProtocol()
        >>> await asyncio.get_event_loop().create_datagram_endpoint(
        >>>     lambda: protocol,
        >>>     remote_addr=("192.168.1.255", DiscoveryProtocol.PORT),
        >>>     allow_broadcast=True,
        >>> )
        >>>
        >>> for _ in range(3):
        >>>     protocol.send_discovery_request()
        >>>     await asyncio.sleep(1)
        >>>
        >>> for mac, ips in protocol.get_discovery_result():
        >>>     print(mac.hex(":"), *ips)
        98:d8:63:a5:9e:5c 192.168.1.5
        98:d8:63:a5:8a:35 192.168.1.8 192.168.1.9
    """

    PORT = 48899

    _DISCOVERY_REQUEST = b"HF-A11ASSISTHREAD"

    _transport: Optional[asyncio.transports.DatagramTransport] = None
    _result: DefaultDict[MacAddress, set]

    def __init__(self):
        self._result = defaultdict(set)

    # implementation of asyncio.DatagramProtocol follows

    def connection_made(self, transport):
        log.debug("Starting discovery protocol")
        self._transport = cast(asyncio.transports.DatagramTransport, transport)

    def datagram_received(self, data: bytes, addr):
        real_ip_str, _port = addr
        real_ip = ipaddress.ip_address(real_ip_str)
        log.debug("Discovery reply received from %s: %s", real_ip, data)
        _reported_ip_str, mac_str, _model = data.decode("ascii").split(",")
        mac = MacAddress.fromhex(mac_str)
        self._result[mac].add(real_ip)

    # public API follows

    def send_discovery_request(self):
        if not self._transport:
            raise ValueError(
                "Transport is not available. "
                "The protocol must be first initiated using `create_datagram_endpoint`."
            )
        log.debug("Sending discovery request")
        self._transport.sendto(self._DISCOVERY_REQUEST)

    def get_discovery_result(self) -> DiscoveryResult:
        return self._result


async def discover_ips_by_mac(
    ip: str, *, broadcast: bool = False, retry: int = 3, sleep: float = 1
) -> DiscoveryResult:
    """
    Discover Skydance Wi-Fi relays.

    Args:
        ip: IP target of discovery protocol. Can be either individual device IP (to get
            its MAC address), or broadcast address (to discover present devices).
        broadcast: Whether the IP is broadcast address. On most systems, requires
            `sudo` to operate (to bind 0.0.0.0).
        retry: How many times to retry sending discovery request.
        sleep: Sleep time between subsequent discovery requests.

    Returns:
        Mapping of found Skydance Wi-Fi relays. Their MAC address is the key and their
        IP addresses are the values (stored in `set`).
    """
    protocol = DiscoveryProtocol()
    await asyncio.get_event_loop().create_datagram_endpoint(
        lambda: protocol,
        remote_addr=(ip, DiscoveryProtocol.PORT),
        allow_broadcast=broadcast,
    )
    for attempt in range(retry):
        if attempt:
            await asyncio.sleep(sleep)
        protocol.send_discovery_request()

    return protocol.get_discovery_result()
