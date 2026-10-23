from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List


def to_decimal(val: Any) -> Decimal:
    if val is None:
        return Decimal("0.00")
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_line_item(
    quantity: int,
    unit_price: float,
    discount_amount: float = 0.00,
    tax_rate: float = 18.00
) -> Dict[str, Decimal]:
    qty = Decimal(quantity)
    rate = to_decimal(unit_price)
    disc = to_decimal(discount_amount)
    tax_pct = to_decimal(tax_rate)

    line_subtotal = (qty * rate) - disc
    if line_subtotal < Decimal("0.00"):
        line_subtotal = Decimal("0.00")

    tax_amount = (line_subtotal * (tax_pct / Decimal("100.00"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total_price = line_subtotal + tax_amount

    return {
        "subtotal": line_subtotal,
        "tax_amount": tax_amount,
        "total_price": total_price,
    }


def calculate_order_totals(
    items_data: List[Dict[str, Any]],
    order_discount: float = 0.00,
    gst_rate: float = 18.00
) -> Dict[str, Decimal]:
    subtotal = Decimal("0.00")

    for item in items_data:
        qty = Decimal(item.get("quantity", 1))
        unit_price = to_decimal(item.get("unit_price", 0))
        item_disc = to_decimal(item.get("discount_amount", 0))
        subtotal += (qty * unit_price) - item_disc

    order_disc = to_decimal(order_discount)
    taxable_value = subtotal - order_disc
    if taxable_value < Decimal("0.00"):
        taxable_value = Decimal("0.00")

    tax_pct = to_decimal(gst_rate)
    gst_amount = (taxable_value * (tax_pct / Decimal("100.00"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total_amount = taxable_value + gst_amount

    return {
        "subtotal": subtotal,
        "discount_amount": order_disc,
        "taxable_value": taxable_value,
        "gst_rate": tax_pct,
        "gst_amount": gst_amount,
        "total_amount": total_amount,
    }
