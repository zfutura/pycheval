from io import BytesIO
from pathlib import Path
from xml.dom.minidom import Document, parseString

from pypdf import PdfReader, PdfWriter
from pypdf.generic import StreamObject

from .pdf_embed import embed_invoice_in_pdf
from .test_data import en16931_einfach

_EXTENSION_NS = "http://www.aiim.org/pdfa/ns/extension/"
_SCHEMA_NS = "http://www.aiim.org/pdfa/ns/schema#"
_PDF_SCHEMA_URI = "http://ns.adobe.com/pdf/1.3/"
_FACTURX_SCHEMA_URI = "urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#"

_XMP_HEAD = (
    '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description rdf:about=""'
    ' xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"'
    ' xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/"'
    ' xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#"'
    ' xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#">'
)
_XMP_PDFAID = (
    "<pdfaid:part>3</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>"
)
_XMP_TAIL = '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="r"?>'

# PDF/A producers such as Typst already declare extension schemas next to
# the PDF/A identification.
_XMP_WITH_SCHEMAS = (
    _XMP_HEAD
    + "<pdfaExtension:schemas><rdf:Bag>"
    + '<rdf:li rdf:parseType="Resource">'
    + "<pdfaSchema:schema>Adobe PDF schema</pdfaSchema:schema>"
    + f"<pdfaSchema:namespaceURI>{_PDF_SCHEMA_URI}</pdfaSchema:namespaceURI>"
    + "<pdfaSchema:prefix>pdf</pdfaSchema:prefix>"
    + "</rdf:li>"
    + "</rdf:Bag></pdfaExtension:schemas>"
    + _XMP_PDFAID
    + _XMP_TAIL
)
_XMP_WITHOUT_SCHEMAS = _XMP_HEAD + _XMP_PDFAID + _XMP_TAIL


def test_embed__existing_extension_schemas(tmp_path: Path) -> None:
    pdf_path = _write_pdf(tmp_path, _XMP_WITH_SCHEMAS)
    xmp = _read_xmp(embed_invoice_in_pdf(pdf_path, en16931_einfach()))
    assert len(xmp.getElementsByTagNameNS(_EXTENSION_NS, "schemas")) == 1
    assert _schema_uris(xmp) == [_PDF_SCHEMA_URI, _FACTURX_SCHEMA_URI]


def test_embed__no_extension_schemas(tmp_path: Path) -> None:
    pdf_path = _write_pdf(tmp_path, _XMP_WITHOUT_SCHEMAS)
    xmp = _read_xmp(embed_invoice_in_pdf(pdf_path, en16931_einfach()))
    assert len(xmp.getElementsByTagNameNS(_EXTENSION_NS, "schemas")) == 1
    assert _schema_uris(xmp) == [_FACTURX_SCHEMA_URI]


def _write_pdf(tmp_path: Path, xmp: str) -> Path:
    writer = PdfWriter()
    writer.add_blank_page(595, 842)
    writer.xmp_metadata = xmp.encode("utf-8")
    path = tmp_path / "input.pdf"
    writer.write(path)
    return path


def _read_xmp(pdf: bytes) -> Document:
    metadata = PdfReader(BytesIO(pdf)).root_object["/Metadata"]
    stream = metadata.get_object()
    assert isinstance(stream, StreamObject)
    return parseString(stream.get_data())


def _schema_uris(xmp: Document) -> list[str]:
    uris = []
    for el in xmp.getElementsByTagNameNS(_SCHEMA_NS, "namespaceURI"):
        text = el.firstChild
        assert text is not None and text.nodeValue is not None
        uris.append(text.nodeValue)
    return uris
