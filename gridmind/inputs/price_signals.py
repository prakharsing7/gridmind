"""Helper functions for constructing PriceSignal objects."""

from __future__ import annotations

from datetime import datetime, timedelta

from ..models.site import PricePeriod, PriceSignal


def build_flat_signal(
    price: float,
    start: datetime,
    end: datetime,
    currency: str = "EUR",
) -> PriceSignal:
    """Build a flat-rate price signal covering [start, end)."""
    return PriceSignal(
        periods=[PricePeriod(start=start, end=end, price=price)],
        currency=currency,
    )


def build_tou_signal(
    peak_price: float,
    cheap_price: float,
    peak_start_hour: int,
    peak_end_hour: int,
    start: datetime,
    end: datetime,
    currency: str = "EUR",
) -> PriceSignal:
    """
    Build a time-of-use price signal with peak and cheap periods.

    Peak period runs from peak_start_hour to peak_end_hour on the first day.
    The cheap period covers the remainder of [start, end).
    """
    peak_start = start.replace(hour=peak_start_hour, minute=0, second=0, microsecond=0)
    peak_end = start.replace(hour=peak_end_hour, minute=0, second=0, microsecond=0)
    if peak_end <= peak_start:
        peak_end += timedelta(days=1)

    periods = []
    if peak_start > start:
        periods.append(PricePeriod(start=start, end=peak_start, price=cheap_price))
    periods.append(PricePeriod(start=peak_start, end=peak_end, price=peak_price))
    if peak_end < end:
        periods.append(PricePeriod(start=peak_end, end=end, price=cheap_price))

    return PriceSignal(periods=periods, currency=currency)
