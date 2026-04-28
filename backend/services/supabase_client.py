"""User-scoped Supabase client.

Wraps `supabase-py` and binds the authenticated user's JWT to every PostgREST
request, so RLS policies stay in effect end-to-end (we never use the
service-role key for user-scoped reads/writes).
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class SupabaseUserClient:
    def __init__(self, jwt: str) -> None:
        self._jwt = jwt
        self._client: Client = self._make_client()

    def _make_client(self) -> Client:
        url = os.environ["SUPABASE_URL"]
        anon = os.environ["SUPABASE_ANON_KEY"]
        client = create_client(url, anon)
        # PostgREST needs the user JWT so RLS evaluates auth.uid() correctly.
        client.postgrest.auth(self._jwt)
        return client

    def _reconnect(self) -> None:
        """Create a fresh client when the HTTP/2 connection drops."""
        logger.info("Reconnecting Supabase client after connection error")
        self._client = self._make_client()

    # ---- reads ---------------------------------------------------------------

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        res = (
            self._client.table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return getattr(res, "data", None) if res else None

    def get_recent_workout_logs(self, user_id: str, days: int = 14) -> list[dict[str, Any]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        res = (
            self._client.table("workout_logs")
            .select("*")
            .eq("user_id", user_id)
            .gte("session_date", cutoff)
            .order("session_date", desc=True)
            .execute()
        )
        return getattr(res, "data", []) or [] if res else []

    def get_recent_check_ins(self, user_id: str, days: int = 14) -> list[dict[str, Any]]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        res = (
            self._client.table("check_ins")
            .select("*")
            .eq("user_id", user_id)
            .gte("check_in_date", cutoff)
            .order("check_in_date", desc=True)
            .execute()
        )
        return getattr(res, "data", []) or [] if res else []

    def get_active_microcycle(self, user_id: str) -> dict[str, Any] | None:
        today = date.today().isoformat()
        res = (
            self._client.table("microcycles")
            .select("*")
            .eq("user_id", user_id)
            .lte("start_date", today)
            .gte("end_date", today)
            .order("created_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )
        return getattr(res, "data", None) if res else None

    # ---- microcycles ---------------------------------------------------------

    def insert_microcycle(self, payload: dict[str, Any]) -> dict[str, Any]:
        res = self._client.table("microcycles").insert(payload).execute()
        rows = getattr(res, "data", []) or [] if res else []
        if not rows:
            raise RuntimeError("microcycle insert returned no rows")
        return rows[0]

    # ---- jobs ----------------------------------------------------------------

    def create_job(self, user_id: str) -> dict[str, Any]:
        res = (
            self._client.table("microcycle_jobs")
            .insert({"user_id": user_id, "status": "pending"})
            .execute()
        )
        rows = getattr(res, "data", []) or [] if res else []
        if not rows:
            raise RuntimeError("job insert returned no rows")
        return rows[0]

    def update_job(self, job_id: str, **fields: Any) -> None:
        try:
            self._client.table("microcycle_jobs").update(fields).eq("id", job_id).execute()
        except Exception:
            self._reconnect()
            self._client.table("microcycle_jobs").update(fields).eq("id", job_id).execute()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        try:
            res = (
                self._client.table("microcycle_jobs")
                .select("*")
                .eq("id", job_id)
                .maybe_single()
                .execute()
            )
            return getattr(res, "data", None) if res else None
        except Exception:
            # HTTP/2 connection may go stale during long Ollama jobs — reconnect
            self._reconnect()
            res = (
                self._client.table("microcycle_jobs")
                .select("*")
                .eq("id", job_id)
                .maybe_single()
                .execute()
            )
            return getattr(res, "data", None) if res else None
