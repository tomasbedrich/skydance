# 3.0.0 (2026-11-21)

**BREAKING CHANGES:**

- `Session.read()` and `Session.write()` are replaced by `Session.request()`,
  which sends a command and returns its reply frame. The frame number is now
  handled by the session, so callers do not have to increment it themselves.

Other changes:

- Frame replies by the payload length field instead of the `TAIL` sequence,
  which may also appear inside a payload (e.g. in a zone name or in a color
  component), and raise `skydance.protocol.FrameError` on a malformed or
  inconsistent frame instead of a `struct.error` or an `AttributeError`.
- Pair a reply with its request by the frame number and the command type, so
  that a reply broadcast to another client is not mistaken for ours. Commands
  declare the expected reply type in `Command.response_type`.
- `Response` exposes `frame_number` and always provides `cmd_data` (an empty
  `bytes` when there is no payload).
- Bound every request with a timeout, retry it once on a fresh connection, and
  fail fast when the relay is not reachable at all.
- Pace commands: at least `Session.PAUSE_BETWEEN_COMMANDS` seconds pass between
  two commands, as the relay cannot handle them faster.

# 2.0.0 (2026-10-08)

- Replace deprecated `pkg_resources` with `importlib.metadata` to fix import on Python 3.14.
- Drop Python 3.8 support.

# 1.0.1 (2024-09-27)

- Fix parsing of `GetNumberOfZonesResponse` (see [#17](https://github.com/tomasbedrich/skydance/pull/17))

# 1.0.0 (2021-10-17)

- Add support for RGBW commands.
- Add zone type detection and parsing.

**BREAKING CHANGES:**

- `skydance.protocol.GetZoneNameCommand` renamed to `skydance.protocol.GetZoneInfoCommand`.
- `skydance.protocol.GetZoneNameResponse` renamed to `skydance.protocol.GetZoneInfoResponse`.

# 0.1.2 (2021-01-17)

- Suppress network errors during session closing.

# 0.1.1 (2020-12-28)

- Fix byte representation of zone IDs higher than 2.

# 0.1.0 (2020-12-27)

- Implement `Session` with connection re-creation in case of its failure.
- Implement Skydance discovery protocol.
- Reverse-engineer more commands.
- Make the library Sans I/O (separate IO and protocol logic).
- Write basic documentation.
- Streamline tests and remove redundant ones.


# 0.0.1 (2020-10-13)

- First public release.
