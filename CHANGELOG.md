# Changelog for PyCheval

PyCheval adheres to [semantic versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2025-07-26

### Added

- Add `embed_facturx_file_in_pdf` and `embed_invoice_in_pdf` functions.
- Export enum `FileRelationship` from top-level module.

### Changed

- Rename `generate` to `generate_xml`.
- The source distribution now includes compiled `.mo` files.

### Fixed

- Trade parties can a maximum of one trade contact. Replace
  `TradeParty.contacts` with `TradeParty.contact`.
- Fix element name `AttachmentBinaryObject` in generated XML.
- Validate that the seller has a tax registration number.
- Validate that the tax amounts match.
- Validate that each line charge has a reason code or reason text.
- `ProductClassification` now requires a `listID` attribute.
- Validate the MIME type of attachments.

## [0.1.0] - 2025-05-07

Initial release.
