from enum import Enum
from typing import Final

FACTURX_FILENAME: Final = "factur-x.xml"
XRECHNUNG_FILENAME: Final = "xrechnung.xml"
FACTURX_XML_VERSION: Final = "1.0"


class FileRelationship(Enum):
    """The relationship between a PDF file and an embedded file.

    * DATA: The embedded file contains data that is displayed in the PDF file.
    * SOURCE: The embedded file is the source data for the PDF file.
    * ALTERNATIVE: The embedded file is an alternative representation of
      the PDF file.
    * SUPPLEMENT: The embedded file contains information that supplements
      the data in the PDF file.
    """

    DATA = "Data"
    SOURCE = "Source"
    ALTERNATIVE = "Alternative"
    SUPPLEMENT = "Supplement"
