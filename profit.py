"""Profit identity: Price - Freight - Payment Installment Fees."""
from typing import Optional

FEE_RATE_PER_INSTALLMENT = 0.015


def installment_fee(payment_value, payment_installments):
    # type: (float, Optional[float]) -> float
    n = int(payment_installments) if payment_installments else 1
    if n < 1:
        n = 1
    return float(payment_value) * FEE_RATE_PER_INSTALLMENT * n


def order_profit(price, freight_value, payment_value, payment_installments):
    return (
        float(price)
        - float(freight_value)
        - installment_fee(payment_value, payment_installments)
    )


def is_loss(profit):
    return float(profit) < 0


def high_installment_risk(payment_installments):
    if payment_installments is None:
        return False
    return float(payment_installments) > 6
