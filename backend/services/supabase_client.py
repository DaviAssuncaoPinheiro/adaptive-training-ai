"""User-scoped Supabase client.

Wraps `supabase-py` and binds the authenticated user's JWT to every PostgREST
request, so RLS policies stay in effect end-to-end (we never use the
service-role key for user-scoped reads/writes).
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

from supabase import Client, create_client


class SupabaseUserClient:
    def __init__(self, jwt: str) -> None:
        url = os.environ["SUPABASE_URL"]
        anon = os.environ["SUPABASE_ANON_KEY"]
        self._client: Client = create_client(url, anon)
        # PostgREST needs the user JWT so RLS evaluates auth.uid() correctly.
        self._client.postgrest.auth(jwt)

    # ---- reads ---------------------------------------------------------------

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return (
            self._client.table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
            .data
        )

    def get_recent_workout_logs(self, user_id: str, days: int = 14) -> list[dict[str, Any]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        return (
            self._client.table("workout_logs")
            .select("*")
            .eq("user_id", user_id)
            .gte("session_date", cutoff)
            .order("session_date", desc=True)
            .execute()
            .data
            or []
        )

    def get_recent_check_ins(self, user_id: str, days: int = 14) -> list[dict[str, Any]]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return (
            self._client.table("check_ins")
            .select("*")
            .eq("user_id", user_id)
            .gte("check_in_date", cutoff)
            .order("check_in_date", desc=True)
            .execute()
            .data
            or []
        )

    def get_active_microcycle(self, user_id: str) -> dict[str, Any] | None:
        today = date.today().isoformat()
        return (
            self._client.table("microcycles")
            .select("*")
            .eq("user_id", user_id)
            .lte("start_date", today)
            .gte("end_date", today)
            .order("created_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
            .data
        )

    # ---- microcycles ---------------------------------------------------------

    def insert_microcycle(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self._client.table("microcycles").insert(payload).execute().data or []
        if not rows:
            raise RuntimeError("microcycle insert returned no rows")
        return rows[0]

    # ---- jobs ----------------------------------------------------------------

    def create_job(self, user_id: str) -> dict[str, Any]:
        rows = (
            self._client.table("microcycle_jobs")
            .insert({"user_id": user_id, "status": "pending"})
            .execute()
            .data
            or []
        )
        if not rows:
            raise RuntimeError("job insert returned no rows")
        return rows[0]

    def update_job(self, job_id: str, **fields: Any) -> None:
        self._client.table("microcycle_jobs").update(fields).eq("id", job_id).execute()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return (
            self._client.table("microcycle_jobs")
            .select("*")
            .eq("id", job_id)
            .maybe_single()
            .execute()
            .data
        )
