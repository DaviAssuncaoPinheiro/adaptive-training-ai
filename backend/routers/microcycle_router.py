"""Microcycle endpoints: async generation + status polling + active fetch."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth.supabase_jwt import AuthedUser, get_current_user
from services.microcycle_generator import GenerationError, generate_microcycle
from services.science_justifier import build_justification
from services.supabase_client import SupabaseUserClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["microcycle"])


class GenerateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    id: str
    status: str
    error: str | None = None
    microcycle_id: str | None = None
    created_at: str | None = None
    finished_at: str | None = None


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate(user: AuthedUser = Depends(get_current_user)) -> GenerateResponse:
    db = SupabaseUserClient(user.jwt)
    job = db.create_job(user.user_id)
    asyncio.create_task(_run_job(job_id=job["id"], user=user))
    return GenerateResponse(job_id=job["id"], status=job["status"])


@router.get("/job/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, user: AuthedUser = Depends(get_current_user)) -> JobStatusResponse:
    db = SupabaseUserClient(user.jwt)
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(**job)


@router.get("/active")
def get_active(user: AuthedUser = Depends(get_current_user)) -> dict[str, Any] | None:
    db = SupabaseUserClient(user.jwt)
    return db.get_active_microcycle(user.user_id)


# ---- background work --------------------------------------------------------

async def _run_job(*, job_id: str, user: AuthedUser) -> None:
    db = SupabaseUserClient(user.jwt)
    db.update_job(job_id, status="running")
    try:
        microcycle = await asyncio.to_thread(_do_generate, user=user, db=db)
        microcycle_payload = microcycle.model_dump(mode="json")
        # Schema's `user_id` is set already; insert returns the row with the
        # generated UUID for `microcycle_id`.
        inserted = db.insert_microcycle(microcycle_payload)
        db.update_job(
            job_id,
            status="done",
            microcycle_id=inserted.get("id"),
            finished_at=_now_iso(),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("microcycle job %s failed", job_id)
        db.update_job(
            job_id,
            status="failed",
            error=str(exc),
            finished_at=_now_iso(),
        )


def _do_generate(*, user: AuthedUser, db: SupabaseUserClient):
    profile = db.get_profile(user.user_id)
    if not profile:
        raise GenerationError("profile not found — finish onboarding first")

    logs = db.get_recent_workout_logs(user.user_id)
    check_ins = db.get_recent_check_ins(user.user_id)

    plan = generate_microcycle(
        user_id=user.user_id,
        profile=profile,
        recent_logs=logs,
        recent_check_ins=check_ins,
    )

    # Replace the LLM-only justification with one grounded in PubMed (RAG).
    # Falls back silently to the original text if the science agent is down,
    # so a flaky vector store never blocks microcycle creation.
    grounded = build_justification(profile=profile, plan=plan)
    if grounded:
        plan.ai_justification = grounded
    return plan


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
