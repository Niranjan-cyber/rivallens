from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


class ProfileSummary(BaseModel):
    id: str
    name: str
    kind: Literal["business", "idea"]
    offering_type: Literal["product", "service"]
    note: str
    competitors_monitored: int
    unread_alerts: int
    last_run_at: datetime | None
    is_demo_data: bool


# Fixture until B03 moves profiles into Supabase (specs §2 ProfileSummary shape).
SEED_PROFILES = [
    ProfileSummary(id="stacknest-demo", name="StackNest", kind="business", offering_type="service", note="Cloud deployment, Pune", competitors_monitored=6, unread_alerts=0, last_run_at=None, is_demo_data=True),
    ProfileSummary(id="quickkart-demo", name="QuickKart", kind="business", offering_type="service", note="Quick commerce, Bengaluru", competitors_monitored=5, unread_alerts=0, last_run_at=None, is_demo_data=True),
    ProfileSummary(id="stride-demo", name="Stride & Co.", kind="business", offering_type="product", note="Running shoes, D2C", competitors_monitored=5, unread_alerts=0, last_run_at=None, is_demo_data=True),
    ProfileSummary(id="qubit-demo", name="Qubit Labs", kind="idea", offering_type="service", note="Quantum computing access", competitors_monitored=4, unread_alerts=0, last_run_at=None, is_demo_data=True),
]


@router.get("")
def list_profiles() -> list[ProfileSummary]:
    return SEED_PROFILES
