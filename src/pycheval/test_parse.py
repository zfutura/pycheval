from collections.abc import Callable
from pathlib import Path
from typing import Final
from xml.etree import ElementTree as ET

import pytest

from pycheval.const import NS_RAM

from .exc import NotFacturXError, UnsupportedProfileError, XMLParseError
from .model import MinimumInvoice
from .parse import parse_xml
from .test_data import (
    basic_einfach,
    basic_wl_einfach,
    en16931_einfach,
    minimum_rechnung,
)

TEST_DATA_PATH: Final = Path(__file__).parent / "test_data"


def test_parse_invalid_xml() -> None:
    with pytest.raises(XMLParseError):
        parse_xml("invalid xml")


def test_parse_wrong_root_element() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?><CrossIndustryInvoice/>"""
    with pytest.raises(NotFacturXError):
        parse_xml(xml)


def test_parse_missing_profile_element() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter/>
  </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>
"""  # noqa: E501
    with pytest.raises(NotFacturXError):
        parse_xml(xml)


def test_parse_empty_profile_id() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
        <ram:ID/>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>
"""  # noqa: E501
    with pytest.raises(UnsupportedProfileError):
        parse_xml(xml)


def test_parse_unknown_profile() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
        <ram:ID>urn:unknown</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>
"""  # noqa: E501
    with pytest.raises(UnsupportedProfileError):
        parse_xml(xml)


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("MINIMUM_Rechnung.xml", minimum_rechnung),
        ("BASIC-WL_Einfach.xml", basic_wl_einfach),
        ("BASIC_Einfach.xml", basic_einfach),
        ("EN16931_Einfach.xml", en16931_einfach),
    ],
)
def test_parse_invoice(
    filename: str, expected: Callable[[], MinimumInvoice]
) -> None:
    parsed_invoice = parse_xml(TEST_DATA_PATH / filename)
    expected_invoice = expected()
    assert parsed_invoice == expected_invoice


@pytest.mark.parametrize(
    "email", ["mailto:test@example.com", "test@example.com"]
)
def test_normalize_email(email: str) -> None:
    root = ET.parse(TEST_DATA_PATH / "BASIC-WL_Einfach.xml").getroot()
    buyer_el = root.find(".//ram:BuyerTradeParty", namespaces={"ram": NS_RAM})
    assert buyer_el is not None
    comm_el = ET.SubElement(buyer_el, "ram:URIUniversalCommunication")
    ET.SubElement(comm_el, "ram:URIID", schemeID="EM").text = email

    invoice = parse_xml(ET.tostring(root, encoding="unicode"))
    assert invoice.buyer.email == "test@example.com"
