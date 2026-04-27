from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo


@dataclass
class LocalMonthSummary:
    year: int
    month: int
    total: Decimal
    count: int


def build_revenue_cache_key(
    property_id: str,
    tenant_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> str:
    period = f"{year}:{month}" if month is not None and year is not None else "latest"
    return f"revenue:{tenant_id}:{property_id}:{period}"


def normalize_total_revenue(total: str) -> float:
    value = Decimal(str(total or "0"))
    normalized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(normalized)


def _to_local_month(check_in_date: datetime, timezone_name: str) -> tuple[int, int]:
    if check_in_date.tzinfo is None:
        check_in_date = check_in_date.replace(tzinfo=timezone.utc)

    try:
        local_date = check_in_date.astimezone(ZoneInfo(timezone_name or "UTC"))
    except Exception:
        local_date = check_in_date.astimezone(timezone.utc)

    return local_date.year, local_date.month


def summarize_revenue_by_local_month(
    rows: List[Dict[str, Any]],
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> LocalMonthSummary:
    if not rows:
        if month is None or year is None:
            now = datetime.now(timezone.utc)
            month = month or now.month
            year = year or now.year
        return LocalMonthSummary(year=year, month=month, total=Decimal("0"), count=0)

    row_months: List[tuple[int, int]] = []
    normalized_rows: List[tuple[int, int, Decimal]] = []

    for row in rows:
        local_year, local_month = _to_local_month(
            row["check_in_date"],
            row.get("timezone", "UTC"),
        )
        amount = Decimal(str(row.get("total_amount") or "0"))
        row_months.append((local_year, local_month))
        normalized_rows.append((local_year, local_month, amount))

    if month is None or year is None:
        inferred_year, inferred_month = max(row_months)
        year = year or inferred_year
        month = month or inferred_month

    total = Decimal("0")
    count = 0
    for local_year, local_month, amount in normalized_rows:
        if local_year == year and local_month == month:
            total += amount
            count += 1

    return LocalMonthSummary(year=year, month=month, total=total, count=count)
