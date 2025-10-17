import datetime
from decimal import Decimal
from typing import Final

from .model import (
    EN16931Invoice,
    EN16931LineItem,
    IncludedNote,
    LineAllowance,
    LineCharge,
    LineItem,
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

TEST_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x02\x00\x00\x00\x02PX\xea\x00\x00\x00&IDAT\x18\xd3c\xfc\xff\xff?\x03n\xc0\xc4\xc0\xc0\xc0\xc0\xc8\x88E\x86\x91\x91\x81\x81\x81\x91\x08\xdd\x83X\x9al\x8f\x01\x00\xdf\x94\t\x11%\xfb\xb4\xe3\x00\x00\x00\x00IEND\xaeB`\x82"  # noqa: E501

TEST_SELLER: Final = TradeParty(
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
    contact=TradeContact(
        "Max Mustermann",
        "Sales",
        phone="+49 123 4567890",
        email="foo@example.com",
    ),
)

TEST_BUYER: Final = TradeParty(
    "Buyer AG",
    PostalAddress("DE"),
)

TEST_EN16931_INVOICE: Final = EN16931Invoice(
    "INV-12345",
    DocumentTypeCode.INVOICE,
    datetime.date(2024, 8, 20),
    TEST_SELLER,
    TEST_BUYER,
    "EUR",
    tax_basis_total_amount=Money("10090.00", "EUR"),
    tax_total_amounts=[Money("1917.10", "EUR")],
    grand_total_amount=Money("12007.10", "EUR"),
    due_payable_amount=Money("12007.10", "EUR"),
    line_total_amount=Money("10090.00", "EUR"),
    tax=[
        Tax(
            Money("1917.10", "EUR"),
            Money("10090.00", "EUR"),
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
                ProductClassification("1234-5679", list_id=ItemTypeCode.ISSN),
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
                LineCharge(
                    Money("0.05", "EUR"), reason="Complexity surcharge"
                ),
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
        ReferenceDocument("REFDOC-1", DocumentTypeCode.INVOICING_DATA_SHEET),
        ReferenceDocument(
            "REFDOC-2",
            DocumentTypeCode.RELATED_DOCUMENT,
            "Test ref doc",
            "https://example.com/refdoc.txt",
            attachment=(TEST_PNG, "image/png", "refdoc.png"),
            reference_type_code=ReferenceQualifierCode.PRICE_LIST_VERSION,
        ),
    ],
    procuring_project=("PROJ-123", "Project X"),
    seller_sepa_creditor_id="ABC-dddd",
    payment_means=[
        PaymentMeans(PaymentMeansCode.BANK_PAYMENT),
    ],
    payment_terms=PaymentTerms(
        due_date=datetime.date(2024, 9, 3),
    ),
)
