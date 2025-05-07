"""Generate Factur-X invoices.

Currently, only the EN 16931/COMFORT profile is supported.
"""

from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET
from base64 import b64encode
from decimal import Decimal

from .const import NS_CII, NS_RAM, NS_UDT
from .model import (
    BasicInvoice,
    BasicWLInvoice,
    DocumentAllowance,
    DocumentCharge,
    EN16931Invoice,
    EN16931LineItem,
    IncludedNote,
    LineAllowance,
    LineCharge,
    LineItem,
    MinimumInvoice,
    PaymentMeans,
    PaymentTerms,
    PostalAddress,
    ProductCharacteristic,
    ProductClassification,
    ReferenceDocument,
    Tax,
    TradeContact,
    TradeParty,
)
from .money import Money
from .quantities import QuantityCode
from .type_codes import (
    AllowanceChargeCode,
    DocumentTypeCode,
    ItemTypeCode,
    PaymentMeansCode,
    ReferenceQualifierCode,
    TaxCategoryCode,
    TextSubjectCode,
)
from .types import ID, DocRef, OptionalQuantity, Quantity

__all__ = [
    "generate",
    "generate_et",
]

#
# XML Utility Functions
#


def xml_date(date: datetime.date) -> str:
    """Format a date for Factur-X XML."""
    return "{:04d}{:02d}{:02d}".format(date.year, date.month, date.day)


#
# Common Elements
#


def _date_element(
    parent: ET.Element, name: str, date: datetime.date
) -> ET.Element:
    el = ET.SubElement(parent, name)
    date_el = ET.SubElement(el, "udt:DateTimeString", format="102")
    date_el.text = "{:04d}{:02d}{:02d}".format(date.year, date.month, date.day)
    return el


def _id_element(parent: ET.Element, name: str, id: str) -> ET.Element:
    el = ET.SubElement(parent, name)
    ET.SubElement(el, "ram:ID").text = id
    return el


def _scheme_id_element(parent: ET.Element, name: str, id: ID) -> ET.Element:
    attrs: dict[str, str] = {}
    if id[1] is not None:
        attrs["schemeID"] = id[1]
    el = ET.SubElement(parent, name, attrs)
    el.text = id[0]
    return el


def _currency_element(
    parent: ET.Element,
    name: str,
    amount: Money,
    default_currency: str,
    *,
    with_currency: bool = False,
) -> ET.Element:
    el = ET.SubElement(parent, name)
    if with_currency or amount.currency != default_currency:
        el.set("currencyID", amount.currency)
    el.text = str(amount.amount)
    return el


def _quantity_element(
    parent: ET.Element, name: str, quantity: Quantity | OptionalQuantity
) -> ET.Element:
    q, unit = quantity
    attribs: dict[str, str] = {}
    if unit is not None:
        attribs["unitCode"] = unit
    el = ET.SubElement(parent, name, attribs)
    el.text = str(q)
    return el


def _email_element(
    parent: ET.Element, name: str, email_address: str
) -> ET.Element:
    el = ET.SubElement(parent, name)
    sub = ET.SubElement(el, "ram:URIID", schemeID="EM")
    sub.text = f"mailto:{email_address}"
    return el


def _address_element(parent: ET.Element, address: PostalAddress) -> None:
    root = ET.SubElement(parent, "ram:PostalTradeAddress")
    if address.post_code is not None:
        ET.SubElement(root, "ram:PostcodeCode").text = address.post_code
    if address.line_one is not None:
        ET.SubElement(root, "ram:LineOne").text = address.line_one
    if address.line_two is not None:
        ET.SubElement(root, "ram:LineTwo").text = address.line_two
    if address.line_three is not None:
        ET.SubElement(root, "ram:LineThree").text = address.line_three
    if address.city is not None:
        ET.SubElement(root, "ram:CityName").text = address.city
    ET.SubElement(root, "ram:CountryID").text = address.country_code
    if address.country_subdivision is not None:
        ET.SubElement(
            root, "ram:CountrySubDivisionName"
        ).text = address.country_subdivision


def _note_element(parent: ET.Element, note: IncludedNote) -> None:
    note_el = ET.SubElement(parent, "ram:IncludedNote")
    ET.SubElement(note_el, "ram:Content").text = note.content
    if note.subject_code is not None:
        ET.SubElement(note_el, "ram:SubjectCode").text = note.subject_code


def _document_element(parent: ET.Element, name: str, id: str | None) -> None:
    if id is None:
        return
    el = ET.SubElement(parent, name)
    ET.SubElement(el, "ram:IssuerAssignedID").text = id


def _generate_trade_party(
    parent: ET.Element, name: str, party: TradeParty
) -> None:
    el = ET.SubElement(parent, name)
    for id in party.ids:
        ET.SubElement(el, "ram:ID").text = id
    for global_id in party.global_ids:
        _scheme_id_element(el, "ram:GlobalID", global_id)
    if party.name is not None:
        ET.SubElement(el, "ram:Name").text = party.name
    if party.description is not None:
        ET.SubElement(el, "ram:Description").text = party.description
    if party.legal_id is not None or party.trading_business_name is not None:
        legal_el = ET.SubElement(el, "ram:SpecifiedLegalOrganization")
        if party.legal_id is not None:
            _scheme_id_element(legal_el, "ram:ID", party.legal_id)
        if party.trading_business_name is not None:
            ET.SubElement(
                legal_el, "ram:TradingBusinessName"
            ).text = party.trading_business_name
    for contact in party.contacts:
        _generate_trade_contact(el, contact)
    if party.address is not None:
        _address_element(el, party.address)
    if party.email is not None:
        _email_element(el, "ram:URIUniversalCommunication", party.email)
    if party.tax_number is not None:
        tax = ET.SubElement(el, "ram:SpecifiedTaxRegistration")
        ET.SubElement(tax, "ram:ID", schemeID="FC").text = party.tax_number
    if party.vat_id is not None:
        tax = ET.SubElement(el, "ram:SpecifiedTaxRegistration")
        ET.SubElement(tax, "ram:ID", schemeID="VA").text = party.vat_id


def _generate_trade_contact(parent: ET.Element, contact: TradeContact) -> None:
    el = ET.SubElement(parent, "ram:DefinedTradeContact")
    if contact.person_name is not None:
        ET.SubElement(el, "ram:PersonName").text = contact.person_name
    if contact.department_name is not None:
        ET.SubElement(el, "ram:DepartmentName").text = contact.department_name
    if contact.phone is not None:
        phone_el = ET.SubElement(el, "ram:TelephoneUniversalCommunication")
        ET.SubElement(phone_el, "ram:CompleteNumber").text = contact.phone
    if contact.email is not None:
        _email_element(el, "ram:EmailURIUniversalCommunication", contact.email)


#
# XML Generation
#


def generate_et(invoice: MinimumInvoice) -> ET.Element:
    """
    Generate a Factur-X invoice as ElementTree.

    >>> from datetime import date
    >>> from decimal import Decimal
    >>> from pycheval.type_codes import DocumentTypeCode
    >>> from pycheval.model import MinimumInvoice, PostalAddress, TradeParty
    >>> invoice = MinimumInvoice(
    ...         "12345",
    ...         DocumentTypeCode.INVOICE,
    ...         date(2024, 8, 22),
    ...         TradeParty("Seller GmbH", PostalAddress("DE")),
    ...         TradeParty("Buyer AG", PostalAddress("DE")),
    ...         "EUR",
    ...         tax_basis_total_amount=(Decimal("10000.00"), "EUR"),
    ...         tax_total_amount=(Decimal("1900.00"), "EUR"),
    ...         grand_total_amount=(Decimal("11900.00"), "EUR"),
    ...         due_payable_amount=(Decimal("11900.00"), "EUR"),
    ... )
    >>> root = generate_et(invoice)
    """

    root = ET.Element(
        "rsm:CrossIndustryInvoice",
        {
            "xmlns:rsm": NS_CII,
            "xmlns:ram": NS_RAM,
            "xmlns:udt": NS_UDT,
        },
    )

    _generate_doc_context(root, invoice)
    _generate_doc(root, invoice)
    _generate_transaction(root, invoice)

    return root


def generate(invoice: MinimumInvoice) -> str:
    """
    Generate a Factur-X invoice as XML string.


    >>> from datetime import date
    >>> from decimal import Decimal
    >>> from pycheval.type_codes import DocumentTypeCode
    >>> from pycheval.model import MinimumInvoice, PostalAddress, TradeParty
    >>> invoice = MinimumInvoice(
    ...         "12345",
    ...         DocumentTypeCode.INVOICE,
    ...         date(2024, 8, 22),
    ...         TradeParty("Seller GmbH", PostalAddress("DE")),
    ...         TradeParty("Buyer AG", PostalAddress("DE")),
    ...         "EUR",
    ...         tax_basis_total_amount=(Decimal("10000.00"), "EUR"),
    ...         tax_total_amount=(Decimal("1900.00"), "EUR"),
    ...         grand_total_amount=(Decimal("11900.00"), "EUR"),
    ...         due_payable_amount=(Decimal("11900.00"), "EUR"),
    ... )
    >>> xml_string = generate(invoice)
    """

    root = generate_et(invoice)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def _generate_doc_context(parent: ET.Element, invoice: MinimumInvoice) -> None:
    doc_ctx = ET.SubElement(parent, "rsm:ExchangedDocumentContext")
    if invoice.business_process_id is not None:
        business_el = ET.SubElement(
            doc_ctx, "ram:BusinessProcessSpecifiedDocumentContextParameter"
        )
        ET.SubElement(business_el, "ram:ID").text = invoice.business_process_id
    # Specify the used profile.
    guideline_el = ET.SubElement(
        doc_ctx, "ram:GuidelineSpecifiedDocumentContextParameter"
    )
    ET.SubElement(guideline_el, "ram:ID").text = invoice.PROFILE_URN


def _generate_doc(parent: ET.Element, invoice: MinimumInvoice) -> None:
    doc = ET.SubElement(parent, "rsm:ExchangedDocument")
    ET.SubElement(doc, "ram:ID").text = invoice.invoice_number
    ET.SubElement(doc, "ram:TypeCode").text = str(invoice.type_code)
    _date_element(doc, "ram:IssueDateTime", invoice.invoice_date)
    if isinstance(invoice, BasicWLInvoice):
        for note in invoice.notes:
            _note_element(doc, note)


def _generate_transaction(parent: ET.Element, invoice: MinimumInvoice) -> None:
    transaction_el = ET.SubElement(parent, "rsm:SupplyChainTradeTransaction")
    if isinstance(invoice, BasicInvoice):
        assert len(invoice.line_items) >= 1  # BG-25
        for li in invoice.line_items:
            _generate_line_item(transaction_el, invoice, li)
    _generate_trade_agreement(transaction_el, invoice)
    _generate_delivery(transaction_el, invoice)
    _generate_settlement(transaction_el, invoice)


def _generate_line_item(
    parent: ET.Element, invoice: BasicInvoice, line_item: LineItem
) -> None:
    li_el = ET.SubElement(
        parent,
        "ram:IncludedSupplyChainTradeLineItem",
    )
    _generate_line_item_doc(li_el, line_item)
    _generate_line_item_product(li_el, line_item)
    _generate_line_trade_agreement(li_el, invoice, line_item)
    _generate_line_delivery(li_el, line_item)
    _generate_line_settlement(li_el, invoice, line_item)


def _generate_line_item_doc(parent: ET.Element, line_item: LineItem) -> None:
    li_doc = ET.SubElement(parent, "ram:AssociatedDocumentLineDocument")
    ET.SubElement(li_doc, "ram:LineID").text = line_item.id
    if isinstance(line_item, EN16931LineItem) and line_item.note is not None:
        _note_element(li_doc, line_item.note)


def _generate_line_item_product(
    parent: ET.Element, line_item: LineItem
) -> None:
    el = ET.SubElement(parent, "ram:SpecifiedTradeProduct")
    if line_item.global_id is not None:
        _scheme_id_element(el, "ram:GlobalID", line_item.global_id)
    if isinstance(line_item, EN16931LineItem):
        if line_item.seller_assigned_id is not None:
            ET.SubElement(
                el, "ram:SellerAssignedID"
            ).text = line_item.seller_assigned_id
        if line_item.buyer_assigned_id is not None:
            ET.SubElement(
                el, "ram:BuyerAssignedID"
            ).text = line_item.buyer_assigned_id
    ET.SubElement(el, "ram:Name").text = line_item.name
    if isinstance(line_item, EN16931LineItem):
        if line_item.description is not None:
            ET.SubElement(el, "ram:Description").text = line_item.description
        for characteristic in line_item.product_characteristics:
            _generate_product_characteristic(el, characteristic)
        for classification in line_item.product_classifications:
            _generate_product_classification(el, classification)
        if line_item.origin_country is not None:
            _id_element(el, "ram:OriginTradeCountry", line_item.origin_country)


def _generate_product_characteristic(
    parent: ET.Element, characteristic: ProductCharacteristic
) -> None:
    c_el = ET.SubElement(parent, "ram:ApplicableProductCharacteristic")
    ET.SubElement(c_el, "ram:Description").text = characteristic.description
    ET.SubElement(c_el, "ram:Value").text = characteristic.value


def _generate_product_classification(
    parent: ET.Element, classification: ProductClassification
) -> None:
    cl_el = ET.SubElement(parent, "ram:DesignatedProductClassification")
    cc_el = ET.SubElement(cl_el, "ram:ClassCode")
    cc_el.text = classification.class_code
    if classification.list_id is not None:
        cc_el.attrib["listID"] = classification.list_id
    if classification.list_version_id is not None:
        cc_el.attrib["listVersionID"] = classification.list_version_id


def _generate_line_trade_agreement(
    parent: ET.Element, invoice: BasicInvoice, line_item: LineItem
) -> None:
    agreement = ET.SubElement(parent, "ram:SpecifiedLineTradeAgreement")
    if isinstance(line_item, EN16931LineItem):
        if line_item.buyer_order_line_id is not None:
            doc_el = ET.SubElement(
                agreement, "ram:BuyerOrderReferencedDocument"
            )
            ET.SubElement(
                doc_el, "ram:LineID"
            ).text = line_item.buyer_order_line_id
        if line_item.gross_unit_price is not None:
            price, quantity = line_item.gross_unit_price
            price_el = ET.SubElement(
                agreement, "ram:GrossPriceProductTradePrice"
            )
            _currency_element(
                price_el, "ram:ChargeAmount", price, invoice.currency_code
            )
            if quantity is not None:
                _quantity_element(price_el, "ram:BasisQuantity", quantity)
            if isinstance(line_item.gross_allowance_or_charge, LineAllowance):
                _generate_allowance_or_charge(
                    price_el,
                    "ram:AppliedTradeAllowanceCharge",
                    invoice,
                    line_item.gross_allowance_or_charge,
                    False,
                )
            elif isinstance(line_item.gross_allowance_or_charge, LineCharge):
                _generate_allowance_or_charge(
                    price_el,
                    "ram:AppliedTradeAllowanceCharge",
                    invoice,
                    line_item.gross_allowance_or_charge,
                    True,
                )
    price_el = ET.SubElement(agreement, "ram:NetPriceProductTradePrice")
    _currency_element(
        price_el,
        "ram:ChargeAmount",
        line_item.net_price,
        invoice.currency_code,
    )
    if line_item.basis_quantity is not None:
        _quantity_element(
            price_el, "ram:BasisQuantity", line_item.basis_quantity
        )


def _generate_line_delivery(parent: ET.Element, line_item: LineItem) -> None:
    delivery_el = ET.SubElement(parent, "ram:SpecifiedLineTradeDelivery")
    _quantity_element(
        delivery_el, "ram:BilledQuantity", line_item.billed_quantity
    )


def _generate_line_settlement(
    parent: ET.Element, invoice: BasicInvoice, line_item: LineItem
) -> None:
    settlement = ET.SubElement(parent, "ram:SpecifiedLineTradeSettlement")
    tax = ET.SubElement(settlement, "ram:ApplicableTradeTax")
    ET.SubElement(tax, "ram:TypeCode").text = "VAT"
    ET.SubElement(tax, "ram:CategoryCode").text = line_item.tax_category
    if line_item.tax_rate is not None:
        ET.SubElement(tax, "ram:RateApplicablePercent").text = str(
            line_item.tax_rate
        )
    if isinstance(line_item, EN16931LineItem):
        if line_item.billing_period is not None:
            start, end = line_item.billing_period
            assert start <= end
            period_el = ET.SubElement(settlement, "ram:BillingSpecifiedPeriod")
            _date_element(period_el, "ram:StartDateTime", start)
            _date_element(period_el, "ram:EndDateTime", end)
    for allowance in line_item.allowances:
        _generate_allowance_or_charge(
            settlement,
            "ram:SpecifiedTradeAllowanceCharge",
            invoice,
            allowance,
            False,
        )
    for charge in line_item.charges:
        _generate_allowance_or_charge(
            settlement,
            "ram:SpecifiedTradeAllowanceCharge",
            invoice,
            charge,
            True,
        )
    summation = ET.SubElement(
        settlement,
        "ram:SpecifiedTradeSettlementLineMonetarySummation",
    )
    _currency_element(
        summation,
        "ram:LineTotalAmount",
        line_item.billed_total,
        invoice.currency_code,
    )
    if isinstance(line_item, EN16931LineItem):
        if line_item.doc_ref is not None:
            _generate_referenced_document(settlement, line_item.doc_ref)
        if line_item.trade_account_id is not None:
            _generate_trade_account(settlement, line_item.trade_account_id)


def _generate_preceding_invoice(
    parent: ET.Element, doc: tuple[str, datetime.date | None]
) -> None:
    id, date = doc
    doc_el = ET.SubElement(parent, "ram:InvoiceReferencedDocument")
    ET.SubElement(doc_el, "ram:IssuerAssignedID").text = id
    if date is not None:
        _date_element(doc_el, "ram:FormattedIssueDateTime", date)


def _generate_referenced_document(parent: ET.Element, doc: DocRef) -> None:
    id, ref_type_code = doc
    doc_el = ET.SubElement(parent, "ram:AdditionalReferencedDocument")
    if id is not None:
        ET.SubElement(doc_el, "ram:IssuerAssignedID").text = id
    ET.SubElement(doc_el, "ram:TypeCode").text = str(
        DocumentTypeCode.INVOICING_DATA_SHEET
    )
    if ref_type_code is not None:
        ET.SubElement(doc_el, "ram:ReferenceTypeCode").text = ref_type_code


def _generate_trade_account(parent: ET.Element, id: str) -> None:
    _id_element(parent, "ram:ReceivableSpecifiedTradeAccountingAccount", id)


def _generate_allowance_or_charge(
    parent: ET.Element,
    name: str,
    invoice: BasicWLInvoice,
    allowance_or_charge: LineAllowance | LineCharge,
    is_charge: bool,
) -> None:
    el = ET.SubElement(parent, name)
    indicator_el = ET.SubElement(el, "ram:ChargeIndicator")
    ET.SubElement(indicator_el, "udt:Indicator").text = (
        "true" if is_charge else "false"
    )
    if allowance_or_charge.percent is not None:
        ET.SubElement(el, "ram:CalculationPercent").text = str(
            allowance_or_charge.percent
        )
    if allowance_or_charge.basis_amount is not None:
        _currency_element(
            el,
            "ram:BasisAmount",
            allowance_or_charge.basis_amount,
            invoice.currency_code,
        )
    _currency_element(
        el,
        "ram:ActualAmount",
        allowance_or_charge.actual_amount,
        invoice.currency_code,
    )
    if allowance_or_charge.reason_code is not None:
        ET.SubElement(el, "ram:ReasonCode").text = str(
            allowance_or_charge.reason_code
        )
    if allowance_or_charge.reason is not None:
        ET.SubElement(el, "ram:Reason").text = allowance_or_charge.reason
    if isinstance(allowance_or_charge, (DocumentAllowance, DocumentCharge)):
        tax_el = ET.SubElement(el, "ram:CategoryTradeTax")
        ET.SubElement(tax_el, "ram:TypeCode").text = "VAT"
        ET.SubElement(tax_el, "ram:CategoryCode").text = str(
            allowance_or_charge.tax_category
        )
        if allowance_or_charge.tax_rate is not None:
            ET.SubElement(tax_el, "ram:RateApplicablePercent").text = str(
                allowance_or_charge.tax_rate
            )


def _generate_trade_agreement(
    parent: ET.Element, invoice: MinimumInvoice
) -> None:
    agreement_el = ET.SubElement(parent, "ram:ApplicableHeaderTradeAgreement")
    if invoice.buyer_reference is not None:
        ET.SubElement(
            agreement_el, "ram:BuyerReference"
        ).text = invoice.buyer_reference
    _generate_trade_party(agreement_el, "ram:SellerTradeParty", invoice.seller)
    _generate_trade_party(agreement_el, "ram:BuyerTradeParty", invoice.buyer)
    if (
        isinstance(invoice, BasicWLInvoice)
        and invoice.seller_tax_representative is not None
    ):
        _generate_trade_party(
            agreement_el,
            "ram:SellerTaxRepresentativeTradeParty",
            invoice.seller_tax_representative,
        )
    if isinstance(invoice, EN16931Invoice):
        _document_element(
            agreement_el,
            "ram:SellerOrderReferencedDocument",
            invoice.seller_order_id,
        )
    _document_element(
        agreement_el,
        "ram:BuyerOrderReferencedDocument",
        invoice.buyer_order_id,
    )
    if isinstance(invoice, BasicWLInvoice):
        _document_element(
            agreement_el,
            "ram:ContractReferencedDocument",
            invoice.contract_id,
        )
    if isinstance(invoice, EN16931Invoice):
        for doc in invoice.referenced_docs:
            _generate_referenced_doc(agreement_el, doc)
        if invoice.procuring_project is not None:
            project_id, project_name = invoice.procuring_project
            project_el = ET.SubElement(
                agreement_el, "ram:SpecifiedProcuringProject"
            )
            ET.SubElement(project_el, "ram:ID").text = project_id
            ET.SubElement(project_el, "ram:Name").text = project_name


def _generate_referenced_doc(
    parent: ET.Element, doc: ReferenceDocument
) -> None:
    el = ET.SubElement(parent, "ram:AdditionalReferencedDocument")
    ET.SubElement(el, "ram:IssuerAssignedID").text = doc.id
    if doc.url is not None:
        ET.SubElement(el, "ram:URIID").text = doc.url
    ET.SubElement(el, "ram:TypeCode").text = str(doc.type_code)
    if doc.name is not None:
        ET.SubElement(el, "ram:Name").text = doc.name
    if doc.attachment is not None:
        content, mime_type, filename = doc.attachment
        attach_el = ET.SubElement(el, "ram:AttachedBinaryObject")
        attach_el.text = b64encode(content).decode("ascii")
        attach_el.set("mimeCode", mime_type)
        attach_el.set("filename", filename)
    if doc.reference_type_code is not None:
        ET.SubElement(
            el, "ram:ReferenceTypeCode"
        ).text = doc.reference_type_code


def _generate_delivery(parent: ET.Element, invoice: MinimumInvoice) -> None:
    delivery_el = ET.SubElement(parent, "ram:ApplicableHeaderTradeDelivery")

    if isinstance(invoice, BasicWLInvoice):
        if invoice.ship_to is not None:
            _generate_trade_party(
                delivery_el, "ram:ShipToTradeParty", invoice.ship_to
            )
        if invoice.delivery_date is not None:
            supply_el = ET.SubElement(
                delivery_el, "ram:ActualDeliverySupplyChainEvent"
            )
            _date_element(
                supply_el, "ram:OccurrenceDateTime", invoice.delivery_date
            )
        if invoice.despatch_advice_id is not None:
            _document_element(
                delivery_el,
                "ram:DespatchAdviceReferencedDocument",
                invoice.despatch_advice_id,
            )
    if isinstance(invoice, EN16931Invoice):
        if invoice.receiving_advice_id is not None:
            _document_element(
                delivery_el,
                "ram:ReceivingAdviceReferencedDocument",
                invoice.receiving_advice_id,
            )


def _generate_settlement(parent: ET.Element, invoice: MinimumInvoice) -> None:
    settlement_el = ET.SubElement(
        parent, "ram:ApplicableHeaderTradeSettlement"
    )
    if isinstance(invoice, BasicWLInvoice):
        if invoice.sepa_reference is not None:
            ET.SubElement(
                settlement_el, "ram:CreditorReferenceID"
            ).text = invoice.sepa_reference
        if invoice.payment_reference is not None:
            ET.SubElement(
                settlement_el, "ram:PaymentReference"
            ).text = invoice.payment_reference
    if isinstance(invoice, EN16931Invoice):
        if invoice.tax_currency_code is not None:
            ET.SubElement(
                settlement_el, "ram:TaxCurrencyCode"
            ).text = invoice.tax_currency_code
    ET.SubElement(
        settlement_el, "ram:InvoiceCurrencyCode"
    ).text = invoice.currency_code

    if isinstance(invoice, BasicWLInvoice):
        if invoice.payee is not None:
            _generate_trade_party(
                settlement_el, "ram:PayeeTradeParty", invoice.payee
            )
        for means in invoice.payment_means:
            _generate_payment_means(settlement_el, means)
        for tax in invoice.tax:
            _generate_tax(settlement_el, invoice, tax)
        if invoice.billing_period is not None:
            billing_period = ET.SubElement(
                settlement_el, "ram:BillingSpecifiedPeriod"
            )
            start, end = invoice.billing_period
            _date_element(billing_period, "ram:StartDateTime", start)
            _date_element(billing_period, "ram:EndDateTime", end)

        for allowance in invoice.allowances:
            _generate_allowance_or_charge(
                settlement_el,
                "ram:SpecifiedTradeAllowanceCharge",
                invoice,
                allowance,
                False,
            )
        for charge in invoice.charges:
            _generate_allowance_or_charge(
                settlement_el,
                "ram:SpecifiedTradeAllowanceCharge",
                invoice,
                charge,
                True,
            )

        if invoice.payment_terms is not None:
            _generate_payment_terms(settlement_el, invoice.payment_terms)

    _generate_summation(settlement_el, invoice)

    if isinstance(invoice, BasicWLInvoice):
        for preceding in invoice.preceding_invoices:
            _generate_preceding_invoice(settlement_el, preceding)
        for ref_id in invoice.receiver_accounting_ids:
            _generate_trade_account(settlement_el, ref_id)


def _generate_payment_means(parent: ET.Element, means: PaymentMeans) -> None:
    means_el = ET.SubElement(
        parent, "ram:SpecifiedTradeSettlementPaymentMeans"
    )
    ET.SubElement(means_el, "ram:TypeCode").text = str(means.type_code)
    if means.information is not None:
        ET.SubElement(means_el, "ram:Information").text = means.information
    if means.card is not None:
        card_id, cardholder = means.card
        card_el = ET.SubElement(
            means_el, "ram:ApplicableTradeSettlementFinancialCard"
        )
        ET.SubElement(card_el, "ram:ID").text = card_id
        if cardholder is not None:
            ET.SubElement(card_el, "ram:CardholderName").text = cardholder
    if means.payer_iban is not None:
        account_el = ET.SubElement(
            means_el, "ram:PayerPartyDebtorFinancialAccount"
        )
        ET.SubElement(account_el, "ram:IBANID").text = means.payer_iban
    if means.payee_account is not None:
        account_el = ET.SubElement(
            means_el, "ram:PayeePartyCreditorFinancialAccount"
        )
        if means.payee_account.iban is not None:
            ET.SubElement(
                account_el, "ram:IBANID"
            ).text = means.payee_account.iban
        if means.payee_account.name is not None:
            ET.SubElement(
                account_el, "ram:AccountName"
            ).text = means.payee_account.name
        if means.payee_account.bank_id is not None:
            ET.SubElement(
                account_el, "ram:ProprietaryID"
            ).text = means.payee_account.bank_id
    if means.payee_bic is not None:
        bic_el = ET.SubElement(
            means_el, "ram:PayeeSpecifiedCreditorFinancialInstitution"
        )
        ET.SubElement(bic_el, "ram:BICID").text = means.payee_bic


def _generate_tax(
    parent: ET.Element, invoice: MinimumInvoice, tax: Tax
) -> None:
    tax_el = ET.SubElement(parent, "ram:ApplicableTradeTax")
    _currency_element(
        tax_el,
        "ram:CalculatedAmount",
        tax.calculated_amount,
        invoice.currency_code,
    )
    ET.SubElement(tax_el, "ram:TypeCode").text = "VAT"
    if tax.exemption_reason is not None:
        ET.SubElement(
            tax_el, "ram:ExemptionReason"
        ).text = tax.exemption_reason
    _currency_element(
        tax_el, "ram:BasisAmount", tax.basis_amount, invoice.currency_code
    )
    ET.SubElement(tax_el, "ram:CategoryCode").text = str(tax.category_code)
    if tax.exemption_reason_code is not None:
        ET.SubElement(tax_el, "ram:ExemptionReasonCode").text = str(
            tax.exemption_reason_code
        )
    if tax.tax_point_date is not None:
        _date_element(tax_el, "ram:TaxPointDate", tax.tax_point_date)
    if tax.due_date_type_code is not None:
        ET.SubElement(tax_el, "ram:DueDateTypeCode").text = str(
            tax.due_date_type_code
        )
    if tax.rate_percent is not None:
        ET.SubElement(tax_el, "ram:RateApplicablePercent").text = str(
            tax.rate_percent
        )


def _generate_payment_terms(parent: ET.Element, terms: PaymentTerms) -> None:
    terms_el = ET.SubElement(parent, "ram:SpecifiedTradePaymentTerms")
    if terms.description is not None:
        ET.SubElement(terms_el, "ram:Description").text = terms.description
    if terms.due_date is not None:
        _date_element(terms_el, "ram:DueDateDateTime", terms.due_date)
    if terms.direct_debit_mandate_id is not None:
        ET.SubElement(
            terms_el, "ram:DirectDebitMandateID"
        ).text = terms.direct_debit_mandate_id


def _generate_summation(parent: ET.Element, invoice: MinimumInvoice) -> None:
    summation = ET.SubElement(
        parent, "ram:SpecifiedTradeSettlementHeaderMonetarySummation"
    )
    if invoice.line_total_amount is not None:
        _currency_element(
            summation,
            "ram:LineTotalAmount",
            invoice.line_total_amount,
            invoice.currency_code,
        )
    if isinstance(invoice, BasicWLInvoice):
        if invoice.charge_total_amount is not None:
            _currency_element(
                summation,
                "ram:ChargeTotalAmount",
                invoice.charge_total_amount,
                invoice.currency_code,
            )
        if invoice.allowance_total_amount is not None:
            _currency_element(
                summation,
                "ram:AllowanceTotalAmount",
                invoice.allowance_total_amount,
                invoice.currency_code,
            )
    _currency_element(
        summation,
        "ram:TaxBasisTotalAmount",
        invoice.tax_basis_total_amount,
        invoice.currency_code,
    )
    for amount in invoice.tax_total_amounts:
        _currency_element(
            summation,
            "ram:TaxTotalAmount",
            amount,
            invoice.currency_code,
            with_currency=True,
        )
    if isinstance(invoice, EN16931Invoice):
        if invoice.rounding_amount is not None:
            _currency_element(
                summation,
                "ram:RoundingAmount",
                invoice.rounding_amount,
                invoice.currency_code,
            )
    _currency_element(
        summation,
        "ram:GrandTotalAmount",
        invoice.grand_total_amount,
        invoice.currency_code,
    )
    if isinstance(invoice, BasicWLInvoice):
        if invoice.prepaid_amount is not None:
            _currency_element(
                summation,
                "ram:TotalPrepaidAmount",
                invoice.prepaid_amount,
                invoice.currency_code,
            )
    _currency_element(
        summation,
        "ram:DuePayableAmount",
        invoice.due_payable_amount,
        invoice.currency_code,
    )


if __name__ == "__main__":
    seller = TradeParty(
        "Seller GmbH",
        PostalAddress(
            "DE", None, "44331", "Test City", "Test Street 42", None, None
        ),
        "seller@example.com",
        vat_id="DE123456789",
        tax_number="123/456/789",
        ids=["SELLER-123"],
        global_ids=[("123456789", "0088")],
        description="being formed",
        legal_id=("DE123456789", "0088"),
        trading_business_name="Great Business",
        contacts=[
            TradeContact("Max Mustermann", phone="+49 123 4567890"),
            TradeContact(None, "Sales", email="foo@example.com"),
        ],
    )
    buyer = TradeParty(
        "Buyer AG",
        PostalAddress("DE"),
    )
    invoice = EN16931Invoice(
        "INV-12345",
        DocumentTypeCode.INVOICE,
        datetime.date(2024, 8, 20),
        seller,
        buyer,
        "EUR",
        tax_basis_total_amount=Money("10090.00", "EUR"),
        tax_total_amounts=[Money("19.00", "EUR")],
        grand_total_amount=Money("10089.00", "EUR"),
        due_payable_amount=Money("10089.00", "EUR"),
        line_total_amount=Money("10090.00", "EUR"),
        tax=[
            Tax(
                Money("33.44", "EUR"),
                Money("1000.00", "EUR"),
                Decimal(19),
                TaxCategoryCode.STANDARD_RATE,
            ),
        ],
        delivery_date=datetime.date(2024, 8, 21),
        notes=[
            IncludedNote("This is a test invoice."),
            IncludedNote(
                "This is seller note.", TextSubjectCode.COMMENTS_BY_SELLER
            ),
        ],
        line_items=[
            LineItem(
                "1",
                "Fixed amount item\nWith multiple lines",
                Money("10000.00", "EUR"),
                (Decimal(1), QuantityCode.PIECE),
                Money("10000.00", "EUR"),
                Decimal("19"),
            ),
            EN16931LineItem(
                "2",
                "Hourly item",
                Money("30.00", "EUR"),
                (Decimal(3), QuantityCode.HOUR),
                Money("90.00", "EUR"),
                Decimal("19"),
                global_id=("9781529044195", "0160"),
                basis_quantity=(Decimal(1), QuantityCode.HOUR),
                description="This is a line item description.",
                note=IncludedNote("This is a line item note."),
                seller_assigned_id="ISBN-44",
                buyer_assigned_id="TT-123",
                product_characteristics=[
                    ProductCharacteristic("color", "red"),
                ],
                product_classifications=[
                    ProductClassification("CLASS"),
                    ProductClassification(
                        "9781529044195",
                        list_id=ItemTypeCode.ISBN,
                        list_version_id="99",
                    ),
                ],
                origin_country="DE",
                buyer_order_line_id="BUY-DOC",
                gross_unit_price=(
                    Money("40.00", "EUR"),
                    (Decimal(1), QuantityCode.HOUR),
                ),
                gross_allowance_or_charge=LineAllowance(
                    Money("10.00", "EUR"),
                    reason_code=AllowanceChargeCode.AHEAD_OF_SCHEDULE,
                ),
                charges=[
                    LineCharge(Money("0.05", "EUR")),
                ],
                allowances=[
                    LineAllowance(
                        Money("1.00", "EUR"),
                        reason_code=AllowanceChargeCode.AHEAD_OF_SCHEDULE,
                        reason="Ahead of schedule",
                        basis_amount=Money("20.00", "EUR"),
                        percent=Decimal("5"),
                    ),
                ],
                billing_period=(
                    datetime.date(2024, 8, 1),
                    datetime.date(2024, 8, 31),
                ),
                doc_ref=("REFDOC-1", None),
            ),
        ],
        buyer_reference="BUYER-1234",
        seller_order_id="SELL-DOC",
        buyer_order_id="BUY-DOC",
        contract_id="CONTRACT-123",
        referenced_docs=[
            ReferenceDocument(
                "REFDOC-1", DocumentTypeCode.INVOICING_DATA_SHEET
            ),
            ReferenceDocument(
                "REFDOC-2",
                DocumentTypeCode.RELATED_DOCUMENT,
                "Test ref doc",
                "https://example.com/refdoc.pdf",
                attachment=(b"PDF content", "application/pdf", "refdoc.pdf"),
                reference_type_code=ReferenceQualifierCode.PRICE_LIST_VERSION,
            ),
        ],
        procuring_project=("PROJ-123", "Project X"),
        sepa_reference="ABC-dddd",
        payment_means=[
            PaymentMeans(PaymentMeansCode.BANK_PAYMENT),
        ],
        payment_terms=PaymentTerms(
            due_date=datetime.date(2024, 9, 3),
        ),
    )
    tree = generate_et(invoice)
    ET.indent(tree)
    print(ET.tostring(tree, encoding="unicode", xml_declaration=True))
