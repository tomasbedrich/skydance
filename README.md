# Overview

A library for communication with Skydance Wi-Fi relays.

<a href="https://www.buymeacoffee.com/tomasbedrich" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 106px !important;" ></a>

[![PyPI Version](https://img.shields.io/pypi/v/skydance.svg)](https://pypi.org/project/skydance)
[![PyPI License](https://img.shields.io/pypi/l/skydance.svg)](https://pypi.org/project/skydance)

The original product is [a Wi-Fi to RF gateway](http://www.iskydance.com/index.php?c=product_show&a=index&id=810) manufactured by Skydance Co. China.

Sometimes, it is re-branded under different names. For example, in the Czech Republic, [it is sold](https://www.t-led.cz/p/ovladac-wifi-dimled-69381) as "dimLED" system.

This aim of this library is to roughly cover capabilities of [the official SkySmart Android application](https://play.google.com/store/apps/details?id=com.lxit.wifirelay&hl=cs&gl=US).

# Setup

## Requirements

* Python 3.9+

## Installation

```text
$ pip install skydance
```

# Usage

The protocol implementation is [Sans I/O](https://sans-io.readthedocs.io/).
You must create the connection and send the byte payloads on your own.
There are some helpers in `skydance.network` built on top of Python's asyncio which helps you to wrap the I/O.

TODO - In meantime, please see `test/test_manual.py`.

# Links
- [Home Assistant reverse engineering forum thread](https://community.home-assistant.io/t/skydance-2-4g-rf/99399)
