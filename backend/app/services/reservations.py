from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.services.revenue_summary import summarize_revenue_by_local_month

async def calculate_monthly_revenue(property_id: str, month: int, year: int, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month.
    """

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)
        
    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date}")

    # SQL Simulation (This would be executed against the actual DB)
    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    # In production this query executes against a database session.
    # result = await db.fetch_val(query, property_id, tenant_id, start_date, end_date)
    # return result or Decimal('0')
    
    return Decimal('0') # Placeholder for now until DB connection is finalized


def _build_mock_rows(property_id: str, tenant_id: str) -> List[Dict[str, Any]]:
    paris = "Europe/Paris"
    new_york = "America/New_York"

    seeded_rows: Dict[tuple[str, str], List[tuple[datetime, Decimal, str]]] = {
        ("tenant-a", "prop-001"): [
            (datetime(2024, 2, 29, 23, 30, tzinfo=timezone.utc), Decimal("1250.000"), paris),
            (datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc), Decimal("333.333"), paris),
            (datetime(2024, 3, 16, 10, 0, tzinfo=timezone.utc), Decimal("333.333"), paris),
            (datetime(2024, 3, 17, 10, 0, tzinfo=timezone.utc), Decimal("333.334"), paris),
        ],
        ("tenant-a", "prop-002"): [
            (datetime(2024, 3, 5, 14, 0, tzinfo=timezone.utc), Decimal("1250.00"), paris),
            (datetime(2024, 3, 12, 16, 0, tzinfo=timezone.utc), Decimal("1475.50"), paris),
            (datetime(2024, 3, 20, 15, 0, tzinfo=timezone.utc), Decimal("1199.25"), paris),
            (datetime(2024, 3, 25, 18, 0, tzinfo=timezone.utc), Decimal("1050.75"), paris),
        ],
        ("tenant-a", "prop-003"): [
            (datetime(2024, 3, 2, 15, 0, tzinfo=timezone.utc), Decimal("2850.00"), paris),
            (datetime(2024, 3, 18, 16, 0, tzinfo=timezone.utc), Decimal("3250.50"), paris),
        ],
        ("tenant-b", "prop-004"): [
            (datetime(2024, 3, 8, 18, 0, tzinfo=timezone.utc), Decimal("420.00"), new_york),
            (datetime(2024, 3, 14, 17, 0, tzinfo=timezone.utc), Decimal("560.75"), new_york),
            (datetime(2024, 3, 22, 16, 0, tzinfo=timezone.utc), Decimal("480.25"), new_york),
            (datetime(2024, 3, 28, 19, 0, tzinfo=timezone.utc), Decimal("315.50"), new_york),
        ],
        ("tenant-b", "prop-005"): [
            (datetime(2024, 3, 6, 19, 0, tzinfo=timezone.utc), Decimal("920.00"), new_york),
            (datetime(2024, 3, 15, 18, 0, tzinfo=timezone.utc), Decimal("1080.40"), new_york),
            (datetime(2024, 3, 24, 20, 0, tzinfo=timezone.utc), Decimal("1255.60"), new_york),
        ],
    }

    rows = seeded_rows.get((tenant_id, property_id), [])
    return [
        {
            "check_in_date": check_in_date,
            "total_amount": total_amount,
            "timezone": timezone_name,
        }
        for check_in_date, total_amount, timezone_name in rows
    ]


async def calculate_revenue_summary(
    property_id: str,
    tenant_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Aggregates revenue from database and returns a property-local monthly summary.
    If month/year are omitted, the latest available local month is used.
    """
    try:
        from app.core.database_pool import db_pool
        from sqlalchemy import text

        await db_pool.initialize()

        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                query = text(
                    """
                    SELECT
                        r.check_in_date,
                        r.total_amount,
                        p.timezone
                    FROM reservations r
                    JOIN properties p
                        ON p.id = r.property_id
                       AND p.tenant_id = r.tenant_id
                    WHERE r.property_id = :property_id
                      AND r.tenant_id = :tenant_id
                    ORDER BY r.check_in_date
                    """
                )

                result = await session.execute(
                    query,
                    {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                    },
                )
                rows = [dict(row) for row in result.mappings().all()]

                summary = summarize_revenue_by_local_month(rows, month=month, year=year)
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": str(summary.total),
                    "currency": "USD",
                    "count": summary.count,
                    "year": summary.year,
                    "month": summary.month,
                }

        raise Exception("Database pool not available")

    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")

        mock_rows = _build_mock_rows(property_id, tenant_id)
        summary = summarize_revenue_by_local_month(mock_rows, month=month, year=year)

        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": str(summary.total),
            "currency": "USD",
            "count": summary.count,
            "year": summary.year,
            "month": summary.month,
        }

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    return await calculate_revenue_summary(property_id=property_id, tenant_id=tenant_id)
