# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [0.1.0] - 2026-03-10

### Added

- Initial HANBD Home Assistant integration release.
- Config flow with account authentication (phone + password).
- Cloud API client with:
  - OAuth member authorization
  - Device list retrieval
  - Device operate command support
  - Request/response logging with sensitive-field redaction
- Platforms:
  - Sensor
  - Binary sensor
  - Button
- Device-level entities for each discovered HANBD device.
- Clean button operation (`CLEAN`) via `/member/device-operate/operate`.
- Device busy error detection and user-friendly error handling in Home Assistant UI.
- HACS metadata and manifest for distribution.

### Changed

- Project identity migrated from prior template/history to HANBD naming and domain (`hanbd`).
- Logger namespace and repository references updated to HANBD project URLs.

### Known limitations

- Coordinator default poll interval is conservative and may be tuned in later versions.
