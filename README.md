# PyCheval – Factur-X/ZUGFeRD parsing and generation library for Python

[![GitHub](https://img.shields.io/github/release/zfutura/pycheval/all.svg)](https://github.com/zfutura/pycheval/releases/)
[![Apache 2.0 License](https://img.shields.io/github/license/zfutura/pycheval)](https://github.com/zfutura/pycheval/blob/main/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/zfutura/pycheval/test-and-lint.yml)](https://github.com/zfutura/pycheval/actions/workflows/test-and-lint)

Factur-X (also called ZUGFeRD in Germany) is a Franco-German standard for
electronic invoices. Structured XML data is embedded in PDF-A/3 files,
allowing invoices to be processed automatically, but still be displayed in
standard PDF readers. Factur-X supports EN 16931, the European standard for
electronic invoicing.

See the [Factur-X website (French)](https://www.factur-x.org/) or
[FeRD website (German)](https://www.ferd-net.de/) for more information.

Currently, this library supports reading and writing XML files according to
Factur-X Version 1.0.07 (aka ZUGFeRD 2.3) in the profiles up to EN 16931
(Comfort).

Generally in scope of this library, but currently not supported are:

* Extended and XRechnung profiles.
* Embedding the XML in PDF files.

**Warning**: This library is still in early development. The API may change
frequently, and not all features are implemented yet.

## Usage

### Generating Factur-X XML

PyCheval supports several profiles of Factur-X. First, you need to create
an instance of the correct profile. Then, you can pass that instance to one
of the generation functions.

```python
from datetime import date
from pycheval import EN16931Invoice, Money, generate

invoice = EN16931Invoice(
    invoice_number="2021-123",
    invoice_date=date(2021, 4, 13),
    grand_total=Money("100.00", "EUR"),
    ...  # See the class documentation for all required and optional fields.
)
xml_string = generate(invoice)
```

### Parsing Factur-X PDF files

PyCheval can parse certain Factur-X PDF files. The parser will return an
instance of the correct profile.

```python
from pycheval import parse_pdf

invoice = parse_pdf(path_or_xml_string)  # MinimumInvoice or a subclass
```

### Printing invoices

To print a formatted Factur-X invoice to the terminal, you can use the
`format_invoice_as_text()` function:

```python
from pycheval import format_invoice_as_text

invoice = EN16931Invoice(...)
print(format_invoice_as_text(invoice))
```
