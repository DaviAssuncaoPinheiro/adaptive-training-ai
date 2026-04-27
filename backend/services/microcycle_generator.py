"""Microcycle generator.

Given a profile, recent workout logs, and recent readiness check-ins, calls
the local LLM (Ollama / llama3.1) to produce a `MicrocycleSchema`-shaped plan,
then enforces fitness-level safety caps before returning it.

Optionally enriches the `ai_justification` field with the RAG agent so it
includes APA citations from PubMed.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from typing import Any

import ollama
from pydantic import ValidationError

from schemas.microcycle import MicrocycleSchema

logger = logging.getLogger(__name__)

LLM_MODEL_ID = os.getenv("MICROCYCLE_MODEL_ID", "llama3.1")

# Per-level safety caps (sets/muscle/week, RPE ceiling). Conservative on
# purpose — safer to under-prescribe than to overtrain a beginner.
SAFETY_CAPS: dict[str, dict[str, int]] = {
    "beginner":     {"max_weekly_sets_per_muscle": 12, "max_rpe_cap": 7},
    "intermediate": {"max_weekly_sets_per_muscle": 16, "max_rpe_cap": 8},
    "advanced":     {"max_weekly_sets_per_muscle": 22, "max_rpe_cap": 9},
}

MICROCYCLE_DAYS = 7


class GenerationError(RuntimeError):
    """Raised when the LLM output cannot be turned into a valid microcycle."""


def generate_microcycle(
    *,
    user_id: str,
    profile: dict[str, Any],
    recent_logs: list[dict[str, Any]],
    recent_check_ins: list[dict[str, Any]],
    start_date: date | None = None,
    rag_justification: str | None = None,
) -> MicrocycleSchema:
    start = start_date or date.today()
    end = start + timedelta(days=MICROCYCLE_DAYS - 1)
    caps = _caps_for(profile.get("fitness_level", "beginner"))

    prompt = _build_prompt(profile, recent_logs, recent_check_ins, caps)
    raw_text = _call_llm(prompt)
    plan = _parse_plan(raw_text)

    plan.update(
        {
            "user_id": user_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "max_weekly_sets_per_muscle": caps["max_weekly_sets_per_muscle"],
            "max_rpe_cap": caps["max_rpe_cap"],
        }
    )
    if rag_justification:
        plan["ai_justification"] = rag_justification
    elif not plan.get("ai_justification"):
        plan["ai_justification"] = "Plano gerado com base no perfil e histórico recente."

    try:
        microcycle = MicrocycleSchema.model_validate(plan)
    except ValidationError as exc:
        raise GenerationError(f"LLM returned invalid microcycle shape: {exc}") from exc

    return _apply_safety_caps(microcycle, caps)


# ---- internals --------------------------------------------------------------

def _caps_for(level: str) -> dict[str, int]:
    return SAFETY_CAPS.get(level, SAFETY_CAPS["beginner"])


def _build_prompt(
    profile: dict[str, Any],
    logs: list[dict[str, Any]],
    check_ins: list[dict[str, Any]],
    caps: dict[str, int],
) -> str:
    equipment = ", ".join(profile.get("available_equipment") or []) or "nenhum equipamento informado"
    log_summary = _summarise_logs(logs)
    readiness_summary = _summarise_check_ins(check_ins)

    return (
        "Você é um técnico de força e condicionamento. Gere UM microciclo "
        "semanal de treino (7 dias) personalizado para o praticante abaixo. "
        "Responda APENAS com JSON válido seguindo exatamente o schema, sem "
        "texto extra, sem markdown.\n\n"
        f"PERFIL:\n"
        f"- Idade: {profile.get('age')} | Peso: {profile.get('weight_kg')} kg | "
        f"Altura: {profile.get('height_cm')} cm\n"
        f"- Nível: {profile.get('fitness_level')}\n"
        f"- Objetivo principal: {profile.get('primary_goal')}\n"
        f"- Equipamentos: {equipment}\n\n"
        f"HISTÓRICO RECENTE (últimos 14 dias):\n{log_summary}\n\n"
        f"PRONTIDÃO RECENTE (últimos 14 dias):\n{readiness_summary}\n\n"
        "REGRAS DE SEGURANÇA (obrigatórias):\n"
        f"- target_rpe de cada exercício deve ser <= {caps['max_rpe_cap']}.\n"
        f"- Volume total semanal por grupo muscular deve respeitar "
        f"~{caps['max_weekly_sets_per_muscle']} séries.\n"
        "- Use SOMENTE exercícios compatíveis com os equipamentos disponíveis.\n"
        "- Inclua 1 a 2 dias de descanso (sem exercícios) na semana.\n\n"
        "SCHEMA JSON ESPERADO (responda exatamente neste formato):\n"
        "{\n"
        '  "ai_justification": "string curta em PT-BR explicando as escolhas",\n'
        '  "workouts": [\n'
        '    {\n'
        '      "session_name": "Push A",\n'
        '      "day_of_week": 1,\n'
        '      "exercises": [\n'
        '        {\n'
        '          "exercise_name": "Supino reto com barra",\n'
        '          "target_sets": 4,\n'
        '          "target_reps": "6-10",\n'
        '          "target_rpe": 7,\n'
        '          "rest_seconds": 120\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        "}\n"
        "day_of_week vai de 1 a 7. Pode haver dias ausentes (descanso). "
        "Retorne SOMENTE o JSON."
    )


def _summarise_logs(logs: list[dict[str, Any]]) -> str:
    if not logs:
        return "Sem registros de treino."
    lines = []
    for log in logs[:8]:
        sets = log.get("sets") or []
        n_sets = len(sets)
        avg_rpe = _avg([s.get("rpe") for s in sets if s.get("rpe") is not None])
        lines.append(
            f"- {log.get('session_date', '')[:10]} {log.get('workout_name', '?')}: "
            f"{n_sets} séries, RPE médio {avg_rpe or 'n/d'}"
        )
    return "\n".join(lines)


def _summarise_check_ins(check_ins: list[dict[str, Any]]) -> str:
    if not check_ins:
        return "Sem check-ins recentes."
    last = check_ins[:5]
    sleep = _avg([c.get("sleep_quality") for c in last])
    energy = _avg([c.get("energy_level") for c in last])
    soreness = _avg([c.get("muscle_soreness") for c in last])
    fatigue = _avg([c.get("fatigue_level") for c in last])
    return (
        f"- Médias últimos {len(last)} check-ins (1-10): "
        f"sono={sleep}, energia={energy}, dor={soreness}, fadiga={fatigue}"
    )


def _avg(values: list[Any]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 1)


def _call_llm(prompt: str) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama.Client(host=host)
    try:
        response = client.generate(
            model=LLM_MODEL_ID,
            prompt=prompt,
            format="json",
            options={"temperature": 0.4},
        )
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"Ollama call failed: {exc}") from exc

    text = response.get("response") if isinstance(response, dict) else getattr(response, "response", "")
    if not text:
        raise GenerationError("Ollama returned an empty response")
    return text


def _parse_plan(raw_text: str) -> dict[str, Any]:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"LLM did not return valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GenerationError("LLM JSON root is not an object")
    return data


def _apply_safety_caps(plan: MicrocycleSchema, caps: dict[str, int]) -> MicrocycleSchema:
    rpe_cap = caps["max_rpe_cap"]
    for workout in plan.workouts:
        for ex in workout.exercises:
            if ex.target_rpe > rpe_cap:
                logger.info(
                    "clamping target_rpe %d -> %d for %s",
                    ex.target_rpe,
                    rpe_cap,
                    ex.exercise_name,
                )
                ex.target_rpe = rpe_cap
    return plan
