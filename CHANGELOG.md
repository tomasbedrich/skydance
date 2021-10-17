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
