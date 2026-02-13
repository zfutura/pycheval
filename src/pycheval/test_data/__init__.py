import datetime
from datetime import date
from decimal import Decimal

from pycheval.model import (
    BasicInvoice,
    BasicWLInvoice,
    DocumentAllowance,
    EN16931Invoice,
    EN16931LineItem,
    IncludedNote,
    LineAllowance,
    LineItem,
    MinimumInvoice,
    PaymentTerms,
    PostalAddress,
    Tax,
    TradeParty,
)
from pycheval.money import Money
from pycheval.quantities import QuantityCode
from pycheval.type_codes import (
    DocumentTypeCode,
    IdentifierSchemeCode,
    TaxCategoryCode,
    TextSubjectCode,
)


def minimum_rechnung() -> MinimumInvoice:
    return MinimumInvoice(
        invoice_number="471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2020, 3, 5),
        seller=TradeParty(
            "Lieferant GmbH",
            PostalAddress("DE"),
            tax_number="201/113/40209",
            vat_id="DE123456789",
        ),
        buyer=TradeParty("Kunden AG Frankreich", None),
        currency_code="EUR",
        tax_basis_total_amount=Money("198.00", "EUR"),
        tax_total_amounts=[Money("37.62", "EUR")],
        grand_total_amount=Money("235.62", "EUR"),
        due_payable_amount=Money("235.62", "EUR"),
    )


def basic_wl_einfach() -> BasicWLInvoice:
    return BasicWLInvoice(
        invoice_number="TX-471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2019, 10, 30),
        currency_code="EUR",
        delivery_date=date(2019, 10, 29),
        seller=TradeParty(
            "Taxiunternehmen TX GmbH",
            PostalAddress(
                "DE", None, "10369", "Berlin", "Lieferantenstraße 20"
            ),
            vat_id="DE123456789",
        ),
        buyer=TradeParty(
            "Taxi-Gast AG Mitte",
            PostalAddress(
                "DE",
                "",
                "13351",
                "Berlin",
                "Hans Mustermann",
                "Kundenstraße 15",
            ),
        ),
        line_total_amount=Money("16.90", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("0.00", "EUR"),
        tax_basis_total_amount=Money("16.90", "EUR"),
        tax=[
            Tax(
                Money("1.18", "EUR"),
                Money("16.90", "EUR"),
                Decimal(7),
                TaxCategoryCode.STANDARD_RATE,
            )
        ],
        tax_total_amounts=[Money("1.18", "EUR")],
        grand_total_amount=Money("18.08", "EUR"),
        due_payable_amount=Money("18.08", "EUR"),
        payment_terms=PaymentTerms(due_date=date(2019, 11, 29)),
        notes=[
            IncludedNote("Rechnung gemäß Taxifahrt vom 29.10.2019"),
            IncludedNote("""Taxiunternehmen TX GmbH\t\t\t\t
Lieferantenstraße 20\t\t\t\t
10369 Berlin\t\t\t\t
Deutschland\t\t\t\t
Geschäftsführer: Hans Mustermann
Handelsregisternummer: H A 123
      """),
            IncludedNote("""Unsere GLN: 4000001123452
Ihre GLN: 4000001987658
Ihre Kundennummer: GE2020211
     """),
        ],
    )


def basic_wl() -> BasicWLInvoice:
    return BasicWLInvoice(
        invoice_number="12345",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2026, 1, 1),
        currency_code="EUR",
        seller=TradeParty(
            "Seller",
            PostalAddress("DE"),
            vat_id="DE123456789",
        ),
        buyer=TradeParty(
            "Buyer",
            PostalAddress("DE"),
        ),
        line_total_amount=Money("100.00", "EUR"),
        tax_basis_total_amount=Money("100.00", "EUR"),
        tax=[
            Tax(
                Money("7.00", "EUR"),
                Money("100.00", "EUR"),
                Decimal(7),
                TaxCategoryCode.STANDARD_RATE,
            )
        ],
        tax_total_amounts=[Money("7.00", "EUR")],
        grand_total_amount=Money("107.00", "EUR"),
        due_payable_amount=Money("107.00", "EUR"),
        payment_terms=PaymentTerms(due_date=date(2026, 2, 1)),
    )


def basic_wl_preceding_invoice() -> BasicWLInvoice:
    invoice = basic_wl()
    invoice.preceding_invoices = [
        ("444433", datetime.date(2026, 3, 12)),
    ]
    return invoice


def basic_einfach() -> BasicInvoice:
    return BasicInvoice(
        invoice_number="471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2020, 3, 5),
        currency_code="EUR",
        delivery_date=date(2020, 3, 5),
        seller=TradeParty(
            "Lieferant GmbH",
            PostalAddress(
                "DE", None, "80333", "München", "Lieferantenstraße 20"
            ),
            tax_number="201/113/40209",
            vat_id="DE123456789",
        ),
        buyer=TradeParty(
            "Kunden AG Mitte",
            PostalAddress(
                "DE",
                None,
                "69876",
                "Frankfurt",
                "Hans Muster",
                "Kundenstraße 15",
            ),
        ),
        line_items=[
            LineItem(
                "1",
                """GTIN: 4012345001235
Unsere Art.-Nr.: TB100A4
Trennblätter A4
        """,
                Money("9.90", "EUR"),
                (Decimal("20.0000"), QuantityCode.PIECE),
                Money("198.00", "EUR"),
                Decimal(19),
                global_id=("4012345001235", IdentifierSchemeCode.GTIN),
            ),
        ],
        line_total_amount=Money("198.00", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("0.00", "EUR"),
        tax_basis_total_amount=Money("198.00", "EUR"),
        tax=[
            Tax(
                Money("37.62", "EUR"),
                Money("198.00", "EUR"),
                Decimal("19.00"),
                TaxCategoryCode.STANDARD_RATE,
            )
        ],
        tax_total_amounts=[Money("37.62", "EUR")],
        grand_total_amount=Money("235.62", "EUR"),
        due_payable_amount=Money("235.62", "EUR"),
        payment_terms=PaymentTerms(due_date=date(2020, 4, 4)),
        notes=[
            IncludedNote("Rechnung gemäß Bestellung vom 01.03.2020."),
            IncludedNote("""Lieferant GmbH\t\t\t\t
Lieferantenstraße 20\t\t\t\t
80333 München\t\t\t\t
Deutschland\t\t\t\t
Geschäftsführer: Hans Muster
Handelsregisternummer: H A 123
      """),
            IncludedNote("""Unsere GLN: 4000001123452
Ihre GLN: 4000001987658
Ihre Kundennummer: GE2020211


Zahlbar innerhalb 30 Tagen netto bis 04.04.2020, 3% Skonto innerhalb 10 Tagen bis 15.03.2020.
      """),  # noqa: E501
        ],
    )


def en16931_einfach() -> EN16931Invoice:
    return EN16931Invoice(
        invoice_number="471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2018, 3, 5),
        currency_code="EUR",
        delivery_date=date(2018, 3, 5),
        seller=TradeParty(
            "Lieferant GmbH",
            PostalAddress(
                "DE", None, "80333", "München", "Lieferantenstraße 20"
            ),
            tax_number="201/113/40209",
            vat_id="DE123456789",
            ids=["549910"],
            global_ids=[("4000001123452", IdentifierSchemeCode.GLN)],
        ),
        buyer=TradeParty(
            "Kunden AG Mitte",
            PostalAddress(
                "DE",
                None,
                "69876",
                "Frankfurt",
                "Kundenstraße 15",
            ),
            ids=["GE2020211"],
        ),
        line_items=[
            EN16931LineItem(
                "1",
                "Trennblätter A4",
                Money("9.9000", "EUR"),
                (Decimal("20.0000"), QuantityCode.PIECE),
                Money("198.00", "EUR"),
                Decimal("19.00"),
                global_id=("4012345001235", IdentifierSchemeCode.GTIN),
                seller_assigned_id="TB100A4",
                gross_unit_price=(Money("9.9000", "EUR"), None),
            ),
            EN16931LineItem(
                "2",
                "Joghurt Banane",
                Money("5.5000", "EUR"),
                (Decimal("50.0000"), QuantityCode.PIECE),
                Money("275.00", "EUR"),
                Decimal("7.00"),
                global_id=("4000050986428", IdentifierSchemeCode.GTIN),
                seller_assigned_id="ARNR2",
                gross_unit_price=(Money("5.5000", "EUR"), None),
            ),
        ],
        line_total_amount=Money("473.00", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("0.00", "EUR"),
        tax_basis_total_amount=Money("473.00", "EUR"),
        tax=[
            Tax(
                Money("19.25", "EUR"),
                Money("275.00", "EUR"),
                Decimal("7.00"),
                TaxCategoryCode.STANDARD_RATE,
            ),
            Tax(
                Money("37.62", "EUR"),
                Money("198.00", "EUR"),
                Decimal("19.00"),
                TaxCategoryCode.STANDARD_RATE,
            ),
        ],
        tax_total_amounts=[Money("56.87", "EUR")],
        grand_total_amount=Money("529.87", "EUR"),
        prepaid_amount=Money("0.00", "EUR"),
        due_payable_amount=Money("529.87", "EUR"),
        payment_terms=PaymentTerms(
            description="Zahlbar innerhalb 30 Tagen netto bis 04.04.2018, "
            "3% Skonto innerhalb 10 Tagen bis 15.03.2018"
        ),
        notes=[
            IncludedNote("Rechnung gemäß Bestellung vom 01.03.2018."),
            IncludedNote(
                """Lieferant GmbH\t\t\t\t
Lieferantenstraße 20\t\t\t\t
80333 München\t\t\t\t
Deutschland\t\t\t\t
Geschäftsführer: Hans Muster
Handelsregisternummer: H A 123
      """,
                TextSubjectCode.REGULATORY_INFORMATION,
            ),
        ],
    )


def en16931_rechnungskorrektur() -> EN16931Invoice:
    return EN16931Invoice(
        invoice_number="RK21012345",
        type_code=DocumentTypeCode.CORRECTION,
        invoice_date=date(2018, 9, 16),
        currency_code="EUR",
        delivery_date=date(2018, 8, 5),
        seller=TradeParty(
            "MUSTERLIEFERANT GMBH",
            PostalAddress(
                "DE", None, "99199", "MUSTERHAUSEN", "BAHNHOFSTRASSE 99"
            ),
            vat_id="DE123456789",
            ids=["549910"],
            global_ids=[("4333741000005", IdentifierSchemeCode.GLN)],
        ),
        buyer=TradeParty(
            "MUSTER-KUNDE GMBH",
            PostalAddress(
                "DE",
                None,
                "40235",
                "DUESSELDORF",
                "KUNDENWEG 88",
            ),
            ids=["009420"],
        ),
        line_items=[
            EN16931LineItem(
                "1",
                "Zitronensäure 100ml",
                billed_total=Money("-5.00", "EUR"),
                gross_unit_price=(Money("1.0000", "EUR"), None),
                net_price=Money("1.0000", "EUR"),
                billed_quantity=(Decimal("-5.0000"), QuantityCode.PIECE),
                tax_rate=Decimal("19.00"),
                global_id=("4123456000014", IdentifierSchemeCode.GLN),
                seller_assigned_id="ZS997",
                description="""Verpackung: Flasche
VKE/Geb: 1
        """,
            ),
            EN16931LineItem(
                "2",
                "Gelierzucker Extra 250g",
                net_price=Money("1.4500", "EUR"),
                billed_quantity=(Decimal("-2.0000"), QuantityCode.PIECE),
                billed_total=Money("-2.90", "EUR"),
                tax_rate=Decimal("7.00"),
                global_id=("4123456000021", IdentifierSchemeCode.GLN),
                seller_assigned_id="GZ250",
                gross_unit_price=(Money("1.5000", "EUR"), None),
                gross_allowance_or_charge=LineAllowance(Money("0.05", "EUR")),
                description="""Verpackung: Karton
VKE/Geb: 1
				
        """,
            ),
        ],
        buyer_order_id="B123456789",
        despatch_advice_id="L87654321012345",
        tax=[
            Tax(
                calculated_amount=Money("-0.92", "EUR"),
                basis_amount=Money("-4.85", "EUR"),
                rate_percent=Decimal("19.00"),
                category_code=TaxCategoryCode.STANDARD_RATE,
            ),
            Tax(
                Money("-0.20", "EUR"),
                Money("-2.82", "EUR"),
                Decimal("7.00"),
                TaxCategoryCode.STANDARD_RATE,
            ),
        ],
        allowances=[
            DocumentAllowance(
                actual_amount=Money("-0.10", "EUR"),
                reason="Rechnungsrabatt 1 -2,00% Basisbetrag: -5,00, "
                "MwSt. % 19,0",
                tax_rate=Decimal("19.00"),
            ),
            DocumentAllowance(
                Money("-0.06", "EUR"),
                reason="Rechnungsrabatt 1 -2,00% Basisbetrag: -2,90, "
                "MwSt. %  7,0",
                tax_rate=Decimal("7.00"),
            ),
            DocumentAllowance(
                Money("-0.05", "EUR"),
                reason="Rechnungsrabatt 2       Basisbetrag: -5,00, "
                "MwSt. % 19,0",
                tax_rate=Decimal("19.00"),
            ),
            DocumentAllowance(
                Money("-0.02", "EUR"),
                reason="Rechnungsrabatt 2       Basisbetrag: -2,90, "
                "MwSt. %  7,0",
                tax_rate=Decimal("7.00"),
            ),
        ],
        line_total_amount=Money("-7.90", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("-0.23", "EUR"),
        tax_basis_total_amount=Money("-7.67", "EUR"),
        tax_total_amounts=[Money("-1.12", "EUR")],
        grand_total_amount=Money("-8.79", "EUR"),
        prepaid_amount=Money("0.00", "EUR"),
        due_payable_amount=Money("-8.79", "EUR"),
        notes=[
            IncludedNote(
                "Es bestehen Rabatt- oder Bonusvereinbarungen.",
                TextSubjectCode.PRICE_CONDITIONS,
            ),
            IncludedNote(
                """MUSTERLIEFERANT GMBH
BAHNHOFSTRASSE 99
99199 MUSTERHAUSEN
Geschäftsführung:
Max Mustermann
USt-IdNr: DE123456789
Telefon: +49 932 431 0
www.musterlieferant.de
HRB Nr. 372876
Amtsgericht Musterstadt
GLN 4304171000002
      """,
                TextSubjectCode.REGULATORY_INFORMATION,
            ),
            IncludedNote(
                """Bei Rückfragen:
Telefon: +49 932 431 500
E-Mail : max.muster@musterlieferant.de
      """
            ),
            IncludedNote("""Ursprungsbeleg-Nr  : R87654321012345
Reklamationsnummer : REKLA-2018-235
      """),
            IncludedNote("""Warenempfänger
GLN 430417088093
MUSTER-MARKT

HAUPTSTRASSE 44
31157 SARSTEDT

Abteilung : 8211
      """),
        ],
    )
