from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Final
from xml.dom.minidom import parseString

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    IndirectObject,
    NameObject,
    create_string_object,
)
from pypdf.xmp import XmpInformation

from .exc import InsufficientPDFError
from .generate import generate_xml
from .model import BasicInvoice, MinimumInvoice
from .pdf_common import FACTURX_FILENAME, FACTURX_XML_VERSION, FileRelationship
from .types import Profile

if TYPE_CHECKING:
    from _typeshed import StrPath

RDF_NS: Final = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
FACTURX_NS: Final = "urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#"

FX_EXTENSION_SCHEMA: Final = """
    <rdf:Description xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/" xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#" xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#" rdf:about="">
      <pdfaExtension:schemas>
        <rdf:Bag>
          <rdf:li rdf:parseType="Resource">
            <pdfaSchema:schema>Factur-X PDFA Extension Schema</pdfaSchema:schema>
            <pdfaSchema:namespaceURI>urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#</pdfaSchema:namespaceURI>
            <pdfaSchema:prefix>fx</pdfaSchema:prefix>
            <pdfaSchema:property>
              <rdf:Seq>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>DocumentFileName</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:category>external</pdfaProperty:category>
                  <pdfaProperty:description>The name of the embedded XML document</pdfaProperty:description>
                </rdf:li>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>DocumentType</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:category>external</pdfaProperty:category>
                  <pdfaProperty:description>The type of the hybrid document in capital letters, e.g. INVOICE or ORDER</pdfaProperty:description>
                </rdf:li>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>Version</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:category>external</pdfaProperty:category>
                  <pdfaProperty:description>The actual version of the standard applying to the embedded XML document</pdfaProperty:description>
                </rdf:li>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>ConformanceLevel</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:category>external</pdfaProperty:category>
                  <pdfaProperty:description>The conformance level of the embedded XML document</pdfaProperty:description>
                </rdf:li>
              </rdf:Seq>
            </pdfaSchema:property>
          </rdf:li>
        </rdf:Bag>
      </pdfaExtension:schemas>
    </rdf:Description>
"""  # noqa: E501


def embed_facturx_file_in_pdf(
    pdf_filename: str | Path,
    xml_filename: StrPath,
    *,
    profile: Profile,
    relationship: FileRelationship = FileRelationship.DATA,
) -> bytes:
    """Embed a Factur-X XML file into a PDF file.

    The input PDF file must already be a valid PDF/A-3 document, otherwise
    the generated PDF won't be a valid Factur-X PDF.

    Returns the modified PDF file as a byte stream.

    The `relationship` parameter specifies the relationship of the
    embedded file to the PDF file. It can be one of the values from
    the `FileRelationship` enum.
    """

    xml_data = Path(xml_filename).read_text(encoding="utf-8")
    return _embed(pdf_filename, xml_data, profile, relationship=relationship)


def embed_invoice_in_pdf(
    pdf_filename: str | Path,
    invoice: MinimumInvoice,
    *,
    relationship: FileRelationship | None = None,
) -> bytes:
    """Embed a Factur-X invoice into a PDF file.

    The input PDF file must already be a valid PDF/A-3 document, otherwise
    the generated PDF won't be a valid Factur-X PDF.

    Returns the modified PDF file as a byte stream.

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

    return _embed(
        pdf_filename, xml_data, invoice.PROFILE_NAME, relationship=relationship
    )


def _embed(
    pdf_filename: str | Path,
    xml_data: str,
    profile: Profile,
    relationship: FileRelationship,
) -> bytes:
    writer = PdfWriter(clone_from=pdf_filename)
    _set_metadata(writer, profile)
    _add_attachment(writer, xml_data, relationship)

    output = BytesIO()
    writer.write_stream(output)
    return output.getvalue()


def _set_metadata(writer: PdfWriter, profile: Profile) -> None:
    # TODO: We can't use writer.xmp_metadata, because that will replace
    # an indirect /Metadata entry in the PDF with a new one.
    meta_o = writer.root_object.get("/Metadata")
    if meta_o is None:
        raise InsufficientPDFError("Missing XMP metadata in PDF file.")
    meta_o = meta_o.get_object()
    meta = XmpInformation(meta_o)

    schema = parseString(FX_EXTENSION_SCHEMA)
    assert schema.documentElement is not None
    del schema.documentElement.attributes["xmlns:rdf"]

    doc = meta.rdf_root.ownerDocument
    assert doc is not None
    meta.rdf_root.appendChild(schema.documentElement)
    root = doc.createElementNS(RDF_NS, "rdf:Description")
    root.setAttribute("rdf:about", "")
    meta.rdf_root.appendChild(root)

    root.attributes["xmlns:fx"] = FACTURX_NS
    for tag, content in [
        ("DocumentType", "INVOICE"),
        ("DocumentFileName", FACTURX_FILENAME),
        ("Version", FACTURX_XML_VERSION),
        ("ConformanceLevel", profile),
    ]:
        el = doc.createElement(f"fx:{tag}")
        el.appendChild(doc.createTextNode(content))
        root.appendChild(el)
    meta_o.set_data(doc.toxml().encode("utf-8"))


def _add_attachment(
    writer: PdfWriter, xml_data: str, relationship: FileRelationship
) -> None:
    writer.add_attachment(
        filename=FACTURX_FILENAME, data=xml_data.encode("utf-8")
    )
    attachment = list(writer.attachment_list)[-1]
    attachment.pdf_object[NameObject("/UF")] = create_string_object(
        FACTURX_FILENAME
    )
    attachment._embedded_file[NameObject("/Subtype")] = NameObject("/text/xml")

    # Get the file specification dictionary from the names tree
    catalog = writer._root_object
    names_dict = catalog["/Names"]
    assert isinstance(names_dict, DictionaryObject), (
        f"/Names is {type(names_dict)}"
    )
    embedded_files = names_dict["/EmbeddedFiles"]
    assert isinstance(embedded_files, DictionaryObject), (
        f"/EmbeddedFiles is {type(embedded_files)}"
    )
    names_array = embedded_files["/Names"]
    assert isinstance(names_array, ArrayObject), (
        f"/Names is {type(names_array)}"
    )
    file_dict = names_array[-1]
    if isinstance(file_dict, IndirectObject):
        file_dict = file_dict.get_object()
    assert isinstance(file_dict, DictionaryObject), (
        f"file_dict is {type(file_dict)}"
    )

    file_dict[NameObject("/AFRelationship")] = NameObject(
        f"/{relationship.value}"
    )

    file_ref = writer._add_object(file_dict)
    names_array[-1] = file_ref

    # Add the file reference to the /AF array in the catalog.
    if NameObject("/AF") not in catalog:
        catalog[NameObject("/AF")] = ArrayObject()
    af_array = catalog[NameObject("/AF")]
    assert isinstance(af_array, ArrayObject), f"/AF is {type(af_array)}"
    if file_ref not in af_array:
        af_array.append(file_ref)


def main() -> None:
    from ._test_data import TEST_EN16931_INVOICE
    from .parse import parse_xml

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} PDF-FILE [XML-FILE]", file=sys.stderr)
        sys.exit(1)
    pdf_filename = sys.argv[1]
    if len(sys.argv) == 2:
        pdf_data = embed_invoice_in_pdf(pdf_filename, TEST_EN16931_INVOICE)
    else:
        invoice = parse_xml(sys.argv[2])
        pdf_data = embed_facturx_file_in_pdf(
            pdf_filename, sys.argv[2], profile=invoice.PROFILE_NAME
        )
    with open("embedded.pdf", "xb") as f:
        f.write(pdf_data)


if __name__ == "__main__":
    main()
