from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.services.revenue_summary import normalize_total_revenue

router = APIRouter()


def _normalize_total_revenue(total: str) -> float:
    return normalize_total_revenue(total)

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(
        property_id=property_id,
        tenant_id=tenant_id,
        month=month,
        year=year,
    )
    
    total_revenue_float = _normalize_total_revenue(revenue_data["total"])
    
    response: Dict[str, Any] = {
        "property_id": revenue_data["property_id"],
        "total_revenue": total_revenue_float,
        "currency": revenue_data["currency"],
        "reservations_count": revenue_data["count"],
    }

    if "month" in revenue_data and "year" in revenue_data:
        response["month"] = revenue_data["month"]
        response["year"] = revenue_data["year"]

    return response
