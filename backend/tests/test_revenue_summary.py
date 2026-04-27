from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.services.revenue_summary import (
    build_revenue_cache_key,
    normalize_total_revenue,
    summarize_revenue_by_local_month,
)


def test_build_revenue_cache_key_includes_tenant_and_period() -> None:
    key = build_revenue_cache_key("prop-001", "tenant-a", month=3, year=2024)

    assert key == "revenue:tenant-a:prop-001:2024:3"


def test_build_revenue_cache_key_defaults_to_latest_period_bucket() -> None:
    key = build_revenue_cache_key("prop-001", "tenant-a")

    assert key == "revenue:tenant-a:prop-001:latest"


def test_normalize_total_revenue_rounds_half_up_to_two_decimals() -> None:
    assert normalize_total_revenue("100.005") == 100.01


def test_summarize_revenue_by_local_month_honors_property_timezone() -> None:
    rows = [
        {
            "check_in_date": datetime(2024, 2, 29, 23, 30, tzinfo=timezone.utc),
            "total_amount": Decimal("1250.000"),
            "timezone": "Europe/Paris",
        },
        {
            "check_in_date": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
            "total_amount": Decimal("333.333"),
            "timezone": "Europe/Paris",
        },
        {
            "check_in_date": datetime(2024, 2, 29, 23, 30, tzinfo=timezone.utc),
            "total_amount": Decimal("999.000"),
            "timezone": "America/New_York",
        },
    ]

    result = summarize_revenue_by_local_month(rows, month=3, year=2024)

    assert result.year == 2024
    assert result.month == 3
    assert result.total == Decimal("1583.333")
    assert result.count == 2


def test_summarize_revenue_by_local_month_uses_latest_month_when_missing() -> None:
    rows = [
        {
            "check_in_date": datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            "total_amount": Decimal("100.000"),
            "timezone": "UTC",
        },
        {
            "check_in_date": datetime(2024, 3, 1, 0, 0, tzinfo=timezone.utc),
            "total_amount": Decimal("200.000"),
            "timezone": "UTC",
        },
    ]

    result = summarize_revenue_by_local_month(rows)

    assert result.year == 2024
    assert result.month == 3
    assert result.total == Decimal("200.000")
    assert result.count == 1
