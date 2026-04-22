"""
Motor de Analise de Estado (State Engine)

Transforma dados brutos de historico (workout_logs, check_ins, microcycles)
em indicadores acionaveis de performance e prontidao do praticante.

Metricas calculadas:
    - Volume semanal total e por exercicio
    - Tonelagem (reps x carga)
    - Intensidade media (RPE medio)
    - Fadiga acumulada (comparativo 7 dias vs 30 dias)
    - Indice de adesao (sessoes realizadas vs prescritas)
    - Volume tolerado (deteccao de queda de performance)
"""

from datetime import date, timedelta
from typing import Any

from backend.database import get_supabase_client


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
RECENT_WINDOW_DAYS = 7
BASELINE_WINDOW_DAYS = 30


# ---------------------------------------------------------------------------
# Busca de dados
# ---------------------------------------------------------------------------

def _fetch_workout_logs(user_id: str, since: date) -> list[dict]:
    """Busca todos os workout_logs do usuario a partir de uma data."""
    supabase = get_supabase_client()
    response = (
        supabase
        .table("workout_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("session_date", since.isoformat())
        .order("session_date", desc=True)
        .execute()
    )
    return response.data or []


def _fetch_check_ins(user_id: str, since: date) -> list[dict]:
    """Busca todos os check-ins do usuario a partir de uma data."""
    supabase = get_supabase_client()
    response = (
        supabase
        .table("check_ins")
        .select("*")
        .eq("user_id", user_id)
        .gte("check_in_date", since.isoformat())
        .order("check_in_date", desc=True)
        .execute()
    )
    return response.data or []


def _fetch_latest_microcycle(user_id: str) -> dict | None:
    """Busca o microciclo mais recente do usuario (ativo ou ultimo finalizado)."""
    supabase = get_supabase_client()
    response = (
        supabase
        .table("microcycles")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )
    return response.data


# ---------------------------------------------------------------------------
# 1. Volume e Intensidade
# ---------------------------------------------------------------------------

def compute_volume_metrics(logs: list[dict]) -> dict:
    """
    Calcula metricas de volume e intensidade a partir dos workout_logs.

    Retorna:
        total_sets: numero total de series realizadas
        total_tonnage: tonelagem total (reps x carga em kg)
        avg_rpe: RPE medio ponderado de todas as series
        volume_per_exercise: dict com sets e tonelagem por exercicio
        sessions_count: numero de sessoes no periodo
        avg_duration_minutes: duracao media das sessoes
    """
    total_sets = 0
    total_tonnage = 0.0
    rpe_sum = 0.0
    rpe_count = 0
    duration_sum = 0
    volume_per_exercise: dict[str, dict[str, Any]] = {}

    for log in logs:
        sets = log.get("sets", [])
        if isinstance(sets, str):
            import json
            sets = json.loads(sets)

        duration_sum += log.get("duration_minutes", 0)

        for s in sets:
            exercise = s.get("exercise_name", "unknown")
            reps = s.get("reps", 0)
            weight = s.get("weight_kg", 0.0)
            rpe = s.get("rpe")

            tonnage = reps * weight
            total_sets += 1
            total_tonnage += tonnage

            if rpe is not None:
                rpe_sum += rpe
                rpe_count += 1

            if exercise not in volume_per_exercise:
                volume_per_exercise[exercise] = {"sets": 0, "tonnage": 0.0, "rpe_values": []}

            volume_per_exercise[exercise]["sets"] += 1
            volume_per_exercise[exercise]["tonnage"] += tonnage
            if rpe is not None:
                volume_per_exercise[exercise]["rpe_values"].append(rpe)

    # Calcular RPE medio por exercicio
    exercise_summary = {}
    for ex, data in volume_per_exercise.items():
        rpe_vals = data["rpe_values"]
        exercise_summary[ex] = {
            "sets": data["sets"],
            "tonnage": round(data["tonnage"], 1),
            "avg_rpe": round(sum(rpe_vals) / len(rpe_vals), 1) if rpe_vals else None,
        }

    sessions_count = len(logs)

    return {
        "total_sets": total_sets,
        "total_tonnage": round(total_tonnage, 1),
        "avg_rpe": round(rpe_sum / rpe_count, 1) if rpe_count > 0 else None,
        "sessions_count": sessions_count,
        "avg_duration_minutes": round(duration_sum / sessions_count, 1) if sessions_count > 0 else 0,
        "volume_per_exercise": exercise_summary,
    }


# ---------------------------------------------------------------------------
# 2. Fadiga Acumulada
# ---------------------------------------------------------------------------

def compute_fatigue_index(check_ins: list[dict]) -> dict:
    """
    Calcula a fadiga acumulada comparando os check-ins recentes (7 dias)
    com a media historica (30 dias).

    Um delta positivo em fatigue/soreness/stress indica AUMENTO (pior).
    Um delta negativo em sleep/energy indica REDUCAO (pior).

    O score_readiness (0-100) consolida tudo em um indicador unico de prontidao.
    """
    if not check_ins:
        return {
            "recent_avg": {},
            "baseline_avg": {},
            "delta": {},
            "readiness_score": None,
            "data_points_recent": 0,
            "data_points_baseline": 0,
        }

    today = date.today()
    recent_cutoff = today - timedelta(days=RECENT_WINDOW_DAYS)

    fields = ["sleep_quality", "energy_level", "muscle_soreness", "stress_level", "fatigue_level"]

    recent = []
    baseline = []

    for ci in check_ins:
        ci_date = ci.get("check_in_date")
        if isinstance(ci_date, str):
            ci_date = date.fromisoformat(ci_date)
        if ci_date >= recent_cutoff:
            recent.append(ci)
        baseline.append(ci)

    def _avg(items: list[dict], field: str) -> float | None:
        values = [item[field] for item in items if item.get(field) is not None]
        return round(sum(values) / len(values), 2) if values else None

    recent_avg = {f: _avg(recent, f) for f in fields}
    baseline_avg = {f: _avg(baseline, f) for f in fields}

    delta = {}
    for f in fields:
        r = recent_avg.get(f)
        b = baseline_avg.get(f)
        if r is not None and b is not None:
            delta[f] = round(r - b, 2)
        else:
            delta[f] = None

    # Readiness Score (0-100)
    # Positivos: sleep_quality, energy_level (maior = melhor)
    # Negativos: muscle_soreness, stress_level, fatigue_level (maior = pior)
    if recent:
        positive = []
        negative = []
        for r_ci in recent:
            positive.append(r_ci.get("sleep_quality", 5))
            positive.append(r_ci.get("energy_level", 5))
            negative.append(r_ci.get("muscle_soreness", 5))
            negative.append(r_ci.get("stress_level", 5))
            negative.append(r_ci.get("fatigue_level", 5))

        avg_positive = sum(positive) / len(positive) if positive else 5.0
        avg_negative = sum(negative) / len(negative) if negative else 5.0

        # Normalizar: positivos contribuem proporcionalmente, negativos inversamente
        # Formula: ((positive_avg / 10) * 50) + (((10 - negative_avg) / 10) * 50)
        readiness_score = round(
            ((avg_positive / 10) * 50) + (((10 - avg_negative) / 10) * 50), 1
        )
        readiness_score = max(0, min(100, readiness_score))
    else:
        readiness_score = None

    return {
        "recent_avg": {k: v for k, v in recent_avg.items() if v is not None},
        "baseline_avg": {k: v for k, v in baseline_avg.items() if v is not None},
        "delta": {k: v for k, v in delta.items() if v is not None},
        "readiness_score": readiness_score,
        "data_points_recent": len(recent),
        "data_points_baseline": len(baseline),
    }


# ---------------------------------------------------------------------------
# 3. Indice de Adesao
# ---------------------------------------------------------------------------

def compute_adherence(logs: list[dict], microcycle: dict | None) -> dict:
    """
    Calcula a razao entre sessoes realizadas vs prescritas no ultimo microciclo.

    Retorna:
        prescribed_sessions: numero de sessoes prescritas no microciclo
        completed_sessions: numero de sessoes logadas no periodo do microciclo
        adherence_rate: percentual (0.0 a 1.0)
    """
    if microcycle is None:
        return {
            "prescribed_sessions": 0,
            "completed_sessions": 0,
            "adherence_rate": None,
            "detail": "Nenhum microciclo encontrado para calcular adesao.",
        }

    workouts = microcycle.get("workouts", [])
    if isinstance(workouts, str):
        import json
        workouts = json.loads(workouts)

    prescribed = len(workouts)

    start_date = microcycle.get("start_date")
    end_date = microcycle.get("end_date")
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    completed = 0
    for log in logs:
        session_date = log.get("session_date", "")
        if isinstance(session_date, str):
            session_date_parsed = date.fromisoformat(session_date.split("T")[0])
        else:
            session_date_parsed = session_date

        if start_date and end_date:
            if start_date <= session_date_parsed <= end_date:
                completed += 1

    adherence_rate = round(completed / prescribed, 2) if prescribed > 0 else None

    return {
        "prescribed_sessions": prescribed,
        "completed_sessions": completed,
        "adherence_rate": adherence_rate,
    }


# ---------------------------------------------------------------------------
# 4. Volume Tolerado
# ---------------------------------------------------------------------------

def compute_tolerated_volume(logs: list[dict]) -> dict:
    """
    Identifica o ponto de queda de performance por exercicio.
    Agrupa sessoes cronologicamente e detecta quando o RPE sobe
    ou a carga cai para o mesmo exercicio, indicando que o volume
    excedeu a capacidade de recuperacao.

    Retorna um dict por exercicio com:
        peak_sets: numero maximo de sets antes da degradacao
        trend: 'stable', 'improving', 'degrading'
    """
    # Agrupar sets por exercicio e data
    exercise_history: dict[str, list[dict]] = {}

    for log in logs:
        session_date = log.get("session_date", "")
        sets = log.get("sets", [])
        if isinstance(sets, str):
            import json
            sets = json.loads(sets)

        for s in sets:
            exercise = s.get("exercise_name", "unknown")
            if exercise not in exercise_history:
                exercise_history[exercise] = []
            exercise_history[exercise].append({
                "date": session_date,
                "reps": s.get("reps", 0),
                "weight_kg": s.get("weight_kg", 0),
                "rpe": s.get("rpe"),
            })

    result = {}
    for exercise, entries in exercise_history.items():
        total_sets = len(entries)
        rpe_values = [e["rpe"] for e in entries if e["rpe"] is not None]
        weights = [e["weight_kg"] for e in entries if e["weight_kg"] > 0]

        # Detectar tendencia via comparacao primeira/segunda metade
        trend = "stable"
        if len(rpe_values) >= 4:
            mid = len(rpe_values) // 2
            first_half_rpe = sum(rpe_values[:mid]) / mid
            second_half_rpe = sum(rpe_values[mid:]) / (len(rpe_values) - mid)

            if second_half_rpe - first_half_rpe > 0.5:
                trend = "degrading"
            elif first_half_rpe - second_half_rpe > 0.5:
                trend = "improving"

        if len(weights) >= 4:
            mid = len(weights) // 2
            first_half_weight = sum(weights[:mid]) / mid
            second_half_weight = sum(weights[mid:]) / (len(weights) - mid)

            if second_half_weight < first_half_weight * 0.95 and trend != "improving":
                trend = "degrading"

        result[exercise] = {
            "total_sets_in_period": total_sets,
            "avg_rpe": round(sum(rpe_values) / len(rpe_values), 1) if rpe_values else None,
            "avg_weight_kg": round(sum(weights) / len(weights), 1) if weights else None,
            "trend": trend,
        }

    return result


# ---------------------------------------------------------------------------
# Orquestrador: Gera o report consolidado
# ---------------------------------------------------------------------------

def build_practitioner_state(user_id: str) -> dict:
    """
    Funcao principal do State Engine.
    Busca todos os dados necessarios e retorna o estado consolidado
    do praticante para consumo pelo modulo de IA (Fase 3).
    """
    today = date.today()
    baseline_since = today - timedelta(days=BASELINE_WINDOW_DAYS)
    recent_since = today - timedelta(days=RECENT_WINDOW_DAYS)

    # Buscar dados
    all_logs = _fetch_workout_logs(user_id, baseline_since)
    recent_logs = [
        log for log in all_logs
        if date.fromisoformat(str(log.get("session_date", "")).split("T")[0]) >= recent_since
    ]
    check_ins = _fetch_check_ins(user_id, baseline_since)
    latest_microcycle = _fetch_latest_microcycle(user_id)

    # Calcular metricas
    weekly_volume = compute_volume_metrics(recent_logs)
    monthly_volume = compute_volume_metrics(all_logs)
    fatigue = compute_fatigue_index(check_ins)
    adherence = compute_adherence(all_logs, latest_microcycle)
    tolerated = compute_tolerated_volume(all_logs)

    return {
        "user_id": user_id,
        "generated_at": today.isoformat(),
        "period": {
            "recent_window_days": RECENT_WINDOW_DAYS,
            "baseline_window_days": BASELINE_WINDOW_DAYS,
        },
        "weekly_volume": weekly_volume,
        "monthly_volume": monthly_volume,
        "fatigue_analysis": fatigue,
        "adherence": adherence,
        "tolerated_volume": tolerated,
    }
