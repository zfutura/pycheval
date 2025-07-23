from typing import Final

from .exc import *  # noqa: F403
from .format import format_invoice_as_text as format_invoice_as_text
from .generate import (
    generate_et as generate_et,
    generate_xml as generate_xml,
)
from .model import *  # noqa: F403
from .money import Money as Money
from .parse import parse_xml as parse_xml
from .pdf_common import FileRelationship as FileRelationship
from .pdf_embed import (
    embed_facturx_file_in_pdf as embed_facturx_file_in_pdf,
    embed_invoice_in_pdf as embed_invoice_in_pdf,
)
from .pdf_parse import parse_pdf as parse_pdf

FACTURX_VERSION: Final = "1.0.07"
ZUGFERD_VERSION: Final = "2.3"
