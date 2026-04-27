"""
Rotas de sessao de treino (workout logs), check-ins e historico.

Endpoints:
    POST /sessions/workout-log      — Registrar uma sessao de treino executada
    GET  /sessions/workout-log/{id} — Buscar um log especifico
    GET  /sessions/history/{uid}    — Historico completo de sessoes
    GET  /sessions/progress/{uid}   — Evolucao de carga por exercicio
    POST /sessions/check-in         — Registrar check-in diario de prontidao
    GET  /sessions/check-ins/{uid}  — Historico de check-ins
"""

import json
import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.database import get_supabase_client
from backend.schemas.session_models import (
    WorkoutLogCreateRequest,
    WorkoutLogResponse,
    CheckInCreateRequest,
    CheckInResponse,
    WorkoutHistoryResponse,
    ExerciseProgressResponse,
    ExerciseProgressEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions & Check-ins"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_sets(raw_sets) -> list[dict]:
    """Normaliza o campo sets que pode vir como JSONB string ou list."""
    if isinstance(raw_sets, str):
        return json.loads(raw_sets)
    return raw_sets if raw_sets else []


# ---------------------------------------------------------------------------
# POST /sessions/workout-log
# ---------------------------------------------------------------------------

@router.post(
    "/workout-log",
    response_model=WorkoutLogResponse,
    status_code=201,
    summary="Registrar sessao de treino executada",
)
async def create_workout_log(payload: WorkoutLogCreateRequest):
    """
    Persiste um registro completo de sessao de treino.
    O campo 'sets' e armazenado como JSONB no banco.
    """
    supabase = get_supabase_client()

    row = {
        "user_id": payload.user_id,
        "session_date": payload.session_date.isoformat(),
        "workout_name": payload.workout_name,
        "duration_minutes": payload.duration_minutes,
        "sets": json.dumps([s.model_dump() for s in payload.sets]),
        "notes": payload.notes,
    }

    try:
        response = supabase.table("workout_logs").insert(row).execute()
    except Exception as e:
        logger.error("Erro ao inserir workout_log: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao registrar sessao: {str(e)}")

    if not response.data:
        raise HTTPException(status_code=500, detail="Falha ao persistir sessao de treino.")

    record = response.data[0]
    record["sets"] = _parse_sets(record.get("sets", []))

    return WorkoutLogResponse(**record)


# ---------------------------------------------------------------------------
# GET /sessions/workout-log/{log_id}
# ---------------------------------------------------------------------------

@router.get(
    "/workout-log/{log_id}",
    response_model=WorkoutLogResponse,
    summary="Buscar um log de treino por ID",
)
async def get_workout_log(log_id: int):
    """Retorna um registro especifico de sessao de treino."""
    supabase = get_supabase_client()

    response = (
        supabase
        .table("workout_logs")
        .select("*")
        .eq("id", log_id)
        .maybe_single()
        .execute()
    )

    if response.data is None:
        raise HTTPException(status_code=404, detail="Log de treino nao encontrado.")

    record = response.data
    record["sets"] = _parse_sets(record.get("sets", []))
    return WorkoutLogResponse(**record)


# ---------------------------------------------------------------------------
# GET /sessions/history/{user_id}
# ---------------------------------------------------------------------------

@router.get(
    "/history/{user_id}",
    response_model=WorkoutHistoryResponse,
    summary="Historico completo de sessoes de treino",
)
async def get_workout_history(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Numero de dias no historico"),
    limit: int = Query(50, ge=1, le=200, description="Maximo de registros"),
):
    """
    Retorna o historico de sessoes de treino do praticante.
    Filtrado por janela de tempo (default: 30 dias).
    """
    supabase = get_supabase_client()
    since = (date.today() - timedelta(days=days)).isoformat()

    response = (
        supabase
        .table("workout_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("session_date", since)
        .order("session_date", desc=True)
        .limit(limit)
        .execute()
    )

    records = response.data or []
    sessions = []
    for r in records:
        r["sets"] = _parse_sets(r.get("sets", []))
        sessions.append(WorkoutLogResponse(**r))

    date_range = None
    if sessions:
        dates = [s.session_date for s in sessions]
        date_range = {
            "from": min(dates).isoformat(),
            "to": max(dates).isoformat(),
        }

    return WorkoutHistoryResponse(
        user_id=user_id,
        total_sessions=len(sessions),
        date_range=date_range,
        sessions=sessions,
    )


# ---------------------------------------------------------------------------
# GET /sessions/progress/{user_id}
# ---------------------------------------------------------------------------

@router.get(
    "/progress/{user_id}",
    response_model=list[ExerciseProgressResponse],
    summary="Evolucao de carga por exercicio",
)
async def get_exercise_progress(
    user_id: str,
    exercise: Optional[str] = Query(None, description="Filtrar por nome do exercicio"),
    days: int = Query(90, ge=1, le=365, description="Janela de dias"),
):
    """
    Retorna a evolucao de carga por exercicio.
    Agrupa os dados por sessao e exercicio, calculando sets totais,
    reps totais, carga maxima e RPE medio por sessao.
    """
    supabase = get_supabase_client()
    since = (date.today() - timedelta(days=days)).isoformat()

    response = (
        supabase
        .table("workout_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("session_date", since)
        .order("session_date", desc=False)
        .execute()
    )

    records = response.data or []

    # Agrupar por exercicio e sessao
    exercise_data: dict[str, list[ExerciseProgressEntry]] = {}

    for record in records:
        sets = _parse_sets(record.get("sets", []))
        session_date = record.get("session_date")
        workout_name = record.get("workout_name", "")

        # Agrupar sets por exercicio dentro desta sessao
        exercise_sets: dict[str, list[dict]] = {}
        for s in sets:
            ex_name = s.get("exercise_name", "unknown")
            if exercise and ex_name.lower() != exercise.lower():
                continue
            if ex_name not in exercise_sets:
                exercise_sets[ex_name] = []
            exercise_sets[ex_name].append(s)

        for ex_name, ex_sets in exercise_sets.items():
            if ex_name not in exercise_data:
                exercise_data[ex_name] = []

            total_sets = len(ex_sets)
            total_reps = sum(s.get("reps", 0) for s in ex_sets)
            max_weight = max((s.get("weight_kg", 0) for s in ex_sets), default=0)
            rpe_values = [s["rpe"] for s in ex_sets if s.get("rpe") is not None]
            avg_rpe = round(sum(rpe_values) / len(rpe_values), 1) if rpe_values else None

            exercise_data[ex_name].append(ExerciseProgressEntry(
                session_date=session_date,
                workout_name=workout_name,
                total_sets=total_sets,
                total_reps=total_reps,
                max_weight_kg=max_weight,
                avg_rpe=avg_rpe,
            ))

    result = []
    for ex_name, entries in sorted(exercise_data.items()):
        result.append(ExerciseProgressResponse(
            exercise_name=ex_name,
            entries=entries,
            total_sessions=len(entries),
        ))

    return result


# ---------------------------------------------------------------------------
# POST /sessions/check-in
# ---------------------------------------------------------------------------

@router.post(
    "/check-in",
    response_model=CheckInResponse,
    status_code=201,
    summary="Registrar check-in diario de prontidao",
)
async def create_check_in(payload: CheckInCreateRequest):
    """
    Persiste um check-in diario de prontidao.
    Se ja existir um check-in para o mesmo user_id + data, realiza upsert.
    """
    supabase = get_supabase_client()

    row = {
        "user_id": payload.user_id,
        "check_in_date": payload.check_in_date.isoformat(),
        "sleep_quality": payload.sleep_quality,
        "energy_level": payload.energy_level,
        "muscle_soreness": payload.muscle_soreness,
        "stress_level": payload.stress_level,
        "fatigue_level": payload.fatigue_level,
    }

    try:
        response = (
            supabase
            .table("check_ins")
            .upsert(row, on_conflict="user_id,check_in_date")
            .execute()
        )
    except Exception as e:
        logger.error("Erro ao inserir check-in: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao registrar check-in: {str(e)}")

    if not response.data:
        raise HTTPException(status_code=500, detail="Falha ao persistir check-in.")

    return CheckInResponse(**response.data[0])


# ---------------------------------------------------------------------------
# GET /sessions/check-ins/{user_id}
# ---------------------------------------------------------------------------

@router.get(
    "/check-ins/{user_id}",
    response_model=list[CheckInResponse],
    summary="Historico de check-ins do praticante",
)
async def get_check_ins(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Janela de dias"),
    limit: int = Query(30, ge=1, le=100, description="Maximo de registros"),
):
    """Retorna os check-ins do praticante ordenados por data decrescente."""
    supabase = get_supabase_client()
    since = (date.today() - timedelta(days=days)).isoformat()

    response = (
        supabase
        .table("check_ins")
        .select("*")
        .eq("user_id", user_id)
        .gte("check_in_date", since)
        .order("check_in_date", desc=True)
        .limit(limit)
        .execute()
    )

    records = response.data or []
    return [CheckInResponse(**r) for r in records]
