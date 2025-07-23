import datetime
from decimal import Decimal

import pytest

from .exc import ModelError
from .model import (
    BasicWLInvoice,
    MinimumInvoice,
    PostalAddress,
    Tax,
    TradeParty,
)
from .money import Money
from .type_codes import DocumentTypeCode


class TestValidateMinimumInvoices:
    def test_seller_must_have_tax_registration(self) -> None:
        _minimum_invoice(seller=_seller(vat_id="DE123456789"))
        with pytest.raises(ModelError):
            _minimum_invoice(seller=_seller(vat_id=None))


class TestValidateBasicWLInvoices:
    def test_seller_must_have_tax_registration(self) -> None:
        _basic_wl_invoice(seller=_seller(vat_id="DE123456789"))
        with pytest.raises(ModelError):
            _basic_wl_invoice(seller=_seller(vat_id=None))
        # If there is a seller tax representative, the seller may not have a
        # tax registration.
        _basic_wl_invoice(
            seller=_seller(vat_id=None),
            seller_tax_representative=_seller_tax_representative(),
        )


def _minimum_invoice(*, seller: TradeParty | None = None) -> MinimumInvoice:
    if seller is None:
        seller = _seller()
    return MinimumInvoice(
        invoice_number="INV-12345",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=datetime.date(2023, 10, 1),
        seller=seller,
        buyer=_buyer(),
        currency_code="EUR",
        tax_basis_total_amount=Money("1000.00", "EUR"),
        tax_total_amounts=[Money("200.00", "EUR")],
        grand_total_amount=Money("1200.00", "EUR"),
        due_payable_amount=Money("1200.00", "EUR"),
    )


def _basic_wl_invoice(
    *,
    seller: TradeParty | None = None,
    seller_tax_representative: TradeParty | None = None,
) -> BasicWLInvoice:
    if seller is None:
        seller = _seller()
    return BasicWLInvoice(
        invoice_number="INV-12345",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=datetime.date(2023, 10, 1),
        seller=seller,
        buyer=_buyer(),
        currency_code="EUR",
        tax_basis_total_amount=Money("1000.00", "EUR"),
        tax_total_amounts=[Money("200.00", "EUR")],
        grand_total_amount=Money("1200.00", "EUR"),
        due_payable_amount=Money("1200.00", "EUR"),
        line_total_amount=Money("1000.00", "EUR"),
        tax=[_tax()],
        seller_tax_representative=seller_tax_representative,
    )


def _seller(*, vat_id: str | None = "DE123456789") -> TradeParty:
    return TradeParty(name="Test Seller", address=_address(), vat_id=vat_id)


def _buyer() -> TradeParty:
    return TradeParty(name="Test Buyer", address=_address())


def _seller_tax_representative() -> TradeParty:
    return TradeParty(
        name="Test Party", address=_address(), vat_id="DE987654321"
    )


def _address() -> PostalAddress:
    return PostalAddress(country_code="DE")


def _tax() -> Tax:
    return Tax(
        calculated_amount=Money("200.00", "EUR"),
        basis_amount=Money("1000.00", "EUR"),
        rate_percent=Decimal("20.00"),
    )
