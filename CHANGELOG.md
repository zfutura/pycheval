# Changelog for PyCheval

PyCheval adheres to [semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- Add `embed_facturx_file_in_pdf` and `embed_invoice_in_pdf` functions.
- Export enum `FileRelationship` from top-level module.

### Changed

- Renamed `generate` to `generate_xml`.

### Fixed

- Trade parties can a maximum of one trade contact. Replace
  `TradeParty.contacts` with `TradeParty.contact`.
- Fix element name `AttachmentBinaryObject` in generated XML.
- Validate that the seller has a tax registration number.
- Validate that the tax amounts match.
- Validate that each line charge has a reason code or reason text.
- `ProductClassification` now requires a `listID` attribute.

## [0.1.0] - 2025-05-07

Initial release.
