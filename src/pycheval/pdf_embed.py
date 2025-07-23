from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from pypdf import PdfWriter
from pypdf.generic import NameObject

from .generate import generate_xml
from .model import BasicInvoice, MinimumInvoice
from .pdf_common import FACTURX_FILENAME, FileRelationship

if TYPE_CHECKING:
    from _typeshed import StrPath


def embed_facturx_file_in_pdf(
    pdf_filename: str | Path,
    xml_filename: StrPath,
    *,
    relationship: FileRelationship = FileRelationship.DATA,
) -> bytes:
    """Embed a Factur-X XML file into a PDF file.

    Returns the PDF file as a byte stream.

    The `relationship` parameter specifies the relationship of the
    embedded file to the PDF file. It can be one of the values from
    the `FileRelationship` enum.
    """

    xml_data = Path(xml_filename).read_text(encoding="utf-8")
    return _embed(pdf_filename, xml_data, relationship=relationship)


def embed_invoice_in_pdf(
    pdf_filename: str | Path,
    invoice: MinimumInvoice,
    *,
    relationship: FileRelationship | None = None,
) -> bytes:
    """Embed a Factur-X invoice into a PDF file.

    Returns the PDF file as a byte stream.

    The `relationship` parameter specifies the relationship of the
    embedded file to the PDF file. It can be one of the values from
    the `FileRelationship` enum. By default, the `Data` relationship
    is used for MINIMUM and BASIC WL profiles, while the `Alternative`
    relationship is used for all other profiles.
    """

    if relationship is None:
        if isinstance(invoice, BasicInvoice):
            relationship = FileRelationship.ALTERNATIVE
        else:
            relationship = FileRelationship.DATA

    xml_data = generate_xml(invoice)

    return _embed(pdf_filename, xml_data, relationship=relationship)


def _embed(
    pdf_filename: str | Path,
    xml_data: str,
    relationship: FileRelationship,
) -> bytes:
    writer = PdfWriter(clone_from=pdf_filename)
    writer.add_attachment(
        filename=FACTURX_FILENAME, data=xml_data.encode("utf-8")
    )
    attachment = list(writer.attachment_list)[-1]
    attachment.pdf_object[NameObject("/AFRelationship")] = NameObject(
        f"/{relationship.value}"
    )
    attachment._embedded_file[NameObject("/Subtype")] = NameObject("/text/xml")

    output = BytesIO()
    writer.write_stream(output)
    return output.getvalue()


def main() -> None:
    from ._test_data import TEST_EN16931_INVOICE

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} PDF-FILE [XML-FILE]", file=sys.stderr)
        sys.exit(1)
    pdf_filename = sys.argv[1]
    if len(sys.argv) == 2:
        pdf_data = embed_invoice_in_pdf(pdf_filename, TEST_EN16931_INVOICE)
    else:
        pdf_data = embed_facturx_file_in_pdf(pdf_filename, sys.argv[2])
    with open("embedded.pdf", "xb") as f:
        f.write(pdf_data)


if __name__ == "__main__":
    main()
