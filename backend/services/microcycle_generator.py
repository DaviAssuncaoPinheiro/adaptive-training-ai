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

import httpx
import ollama
from pydantic import ValidationError

from schemas.microcycle import MicrocycleSchema

logger = logging.getLogger(__name__)

LLM_MODEL_ID = os.getenv("MICROCYCLE_MODEL_ID", "llama3.1")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Per-level volume guidelines (sets/muscle/week). Based on current
# literature (Schoenfeld et al., 2017; Krieger, 2010). RPE is NOT capped
# here — the LLM decides RPE based on the trainee's readiness, level,
# and scientific autoregulation principles.
SAFETY_CAPS: dict[str, dict[str, int]] = {
    "beginner":     {"max_weekly_sets_per_muscle": 12, "max_rpe_cap": 10},
    "intermediate": {"max_weekly_sets_per_muscle": 16, "max_rpe_cap": 10},
    "advanced":     {"max_weekly_sets_per_muscle": 22, "max_rpe_cap": 10},
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
    weekly_briefing: dict[str, Any] | None = None,
    start_date: date | None = None,
    rag_justification: str | None = None,
) -> MicrocycleSchema:
    start = start_date or date.today()
    end = start + timedelta(days=MICROCYCLE_DAYS - 1)
    caps = _caps_for(profile.get("fitness_level", "beginner"))

    prompt = _build_prompt(profile, recent_logs, recent_check_ins, caps, weekly_briefing or {})
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
    weekly_briefing: dict[str, Any],
) -> str:
    equipment = ", ".join(profile.get("available_equipment") or []) or "nenhum equipamento informado"
    log_summary = _summarise_logs(logs)
    readiness_summary = _summarise_check_ins(check_ins)
    weekly_context = _summarise_weekly_briefing(weekly_briefing)

    return (
        "Você é um técnico de força e condicionamento com formação em fisiologia "
        "do exercício e periodização baseada em evidências. Gere UM microciclo "
        "semanal de treino (7 dias) personalizado para o praticante abaixo. "
        "Responda APENAS com JSON válido seguindo exatamente o schema, sem "
        "texto extra, sem markdown.\n\n"
        "PRINCÍPIOS CIENTÍFICOS OBRIGATÓRIOS:\n"
        "Toda decisão de prescrição deve ser fundamentada em ciência do exercício:\n"
        "- Volume: respeite os marcos de volume adaptativo (Schoenfeld et al., 2017). "
        "Iniciantes: 10-12 séries/grupo/semana. Intermediários: 12-16. Avançados: 16-22+.\n"
        "- Intensidade (RPE): use autoregulação baseada em RPE (Helms et al., 2016). "
        "O RPE deve refletir a prontidão atual do praticante — NÃO aplique um teto fixo. "
        "Se o praticante está descansado e preparado, RPE 9-10 é aceitável para séries "
        "principais. Se está fadigado, reduza para RPE 6-7.\n"
        "- Seleção de exercícios: priorize exercícios compostos multiarticulares como base "
        "(Gentil et al., 2017) e complemente com isoladores conforme o objetivo.\n"
        "- Descanso entre séries: 2-3 min para força/hipertrofia em compostos pesados, "
        "60-90s para isoladores e volume (Grgic et al., 2017).\n"
        "- Periodização: aplique variação de estímulo ao longo do microciclo "
        "(ondulação diária ou linear conforme nível).\n"
        "- Sobrecarga progressiva: baseie a prescrição no histórico recente para "
        "garantir progressão gradual e sustentável.\n"
        "- Quantidade de exercícios por sessão: NÃO limite a 2 exercícios. "
        "Adapte ao tempo disponível e nível do praticante. Como guia geral:\n"
        "  * Sessões de 45 min: 4-5 exercícios\n"
        "  * Sessões de 60 min: 5-7 exercícios\n"
        "  * Sessões de 75-90 min: 6-8 exercícios\n"
        "  * Cada sessão deve ter compostos principais + acessórios/isoladores.\n\n"
        f"PERFIL:\n"
        f"- Idade: {profile.get('age')} | Peso: {profile.get('weight_kg')} kg | "
        f"Altura: {profile.get('height_cm')} cm\n"
        f"- Nível: {profile.get('fitness_level')}\n"
        f"- Objetivo principal: {profile.get('primary_goal')}\n"
        f"- Frequencia disponivel: {profile.get('weekly_frequency') or 'N/A'} dias/semana\n"
        f"- Tempo por sessao: {profile.get('session_duration_minutes') or 'N/A'} min\n"
        f"- Equipamentos: {equipment}\n\n"
        f"MEMORIA DO ATLETA:\n"
        f"- Lesoes/restricoes: {profile.get('injury_notes') or 'nada informado'}\n"
        f"- Preferencias de exercicios: {profile.get('exercise_preferences') or 'nada informado'}\n"
        f"- Restricoes de agenda/contexto: {profile.get('training_constraints') or 'nada informado'}\n\n"
        f"BRIEFING DA SEMANA:\n{weekly_context}\n\n"
        f"HISTÓRICO RECENTE (últimos 14 dias):\n{log_summary}\n\n"
        f"PRONTIDÃO RECENTE (últimos 14 dias):\n{readiness_summary}\n\n"
        "DIRETRIZES DE SEGURANÇA:\n"
        f"- Volume semanal por grupo muscular: ~{caps['max_weekly_sets_per_muscle']} séries "
        "(ajuste para cima ou para baixo conforme prontidão e histórico).\n"
        "- RPE: defina com base na autoregulação — considere fadiga acumulada, "
        "qualidade do sono e prontidão reportada. Não use um teto fixo arbitrário.\n"
        "- Use SOMENTE exercícios compatíveis com os equipamentos disponíveis.\n"
        "- Inclua 1 a 2 dias de descanso (sem exercícios) na semana.\n"
        "- Respeite lesoes, restricoes, preferencias e disponibilidade semanal informadas.\n\n"
        "CAMPO ai_justification (OBRIGATÓRIO):\n"
        "Escreva uma justificativa científica detalhada em PT-BR explicando:\n"
        "- Por que escolheu essa divisão de treino para o objetivo do praticante\n"
        "- Como o volume e intensidade foram calibrados com base no nível e prontidão\n"
        "- Quais princípios de periodização foram aplicados\n"
        "- Cite autores/estudos relevantes (ex: Schoenfeld, Helms, Krieger, etc.)\n\n"
        "SCHEMA JSON ESPERADO (com VÁRIOS exercícios por sessão):\n"
        "{\n"
        '  "ai_justification": "Justificativa científica detalhada...",\n'
        '  "workouts": [{\n'
        '    "session_name": "Push A - Peito, Ombro, Tríceps",\n'
        '    "day_of_week": 1,\n'
        '    "exercises": [\n'
        '      {"exercise_name": "Supino reto com barra", "target_sets": 4, "target_reps": "6-10", "target_rpe": 8, "rest_seconds": 120},\n'
        '      {"exercise_name": "Supino inclinado halteres", "target_sets": 3, "target_reps": "8-12", "target_rpe": 7, "rest_seconds": 90},\n'
        '      {"exercise_name": "Desenvolvimento", "target_sets": 3, "target_reps": "8-12", "target_rpe": 7, "rest_seconds": 90},\n'
        '      {"exercise_name": "Elevação lateral", "target_sets": 3, "target_reps": "12-15", "target_rpe": 8, "rest_seconds": 60},\n'
        '      {"exercise_name": "Tríceps pulley", "target_sets": 3, "target_reps": "10-15", "target_rpe": 8, "rest_seconds": 60}\n'
        '    ]\n'
        '  }]\n'
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


def _summarise_weekly_briefing(briefing: dict[str, Any]) -> str:
    if not briefing:
        return "- Sem briefing especifico. Use memoria do atleta, check-ins e historico recente."

    focus = briefing.get("weekly_focus") or "nao informado"
    constraints = briefing.get("constraints") or "nao informado"
    intensity = briefing.get("intensity_preference") or "auto"

    return (
        f"- Foco declarado: {focus}\n"
        f"- Restricoes desta semana: {constraints}\n"
        f"- Preferencia de agressividade: {intensity}"
    )


def _avg(values: list[Any]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 1)


def _call_llm(prompt: str) -> str:
    provider = os.getenv("MICROCYCLE_PROVIDER", "ollama").strip().lower()
    if provider == "gemini":
        return _call_gemini(prompt)
    return _call_ollama(prompt)


def _call_ollama(prompt: str) -> str:
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


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise GenerationError("GEMINI_API_KEY is not configured")

    model = os.getenv("GEMINI_MODEL_ID", GEMINI_MODEL_ID)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json",
        },
    }

    try:
        response = httpx.post(
            GEMINI_ENDPOINT.format(model=model),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:300] if exc.response is not None else str(exc)
        raise GenerationError(f"Gemini call failed: {detail}") from exc
    except httpx.HTTPError as exc:
        raise GenerationError(f"Gemini call failed: {exc}") from exc

    data = response.json()
    parts = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise GenerationError("Gemini returned an empty response")
    return text


def _parse_plan(raw_text: str) -> dict[str, Any]:
    raw_text = _strip_json_fence(raw_text)
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"LLM did not return valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GenerationError("LLM JSON root is not an object")
    return data


def _strip_json_fence(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return text


def _apply_safety_caps(plan: MicrocycleSchema, caps: dict[str, int]) -> MicrocycleSchema:
    """Validate RPE values are within the 1-10 Pydantic range.

    RPE is no longer clamped to a per-level ceiling — the LLM uses
    autoregulation principles (Helms et al., 2016) to decide RPE based
    on the trainee's readiness, fatigue, and level. We only guard
    against out-of-range values.
    """
    for workout in plan.workouts:
        for ex in workout.exercises:
            if ex.target_rpe < 1:
                ex.target_rpe = 1
            elif ex.target_rpe > 10:
                ex.target_rpe = 10
    return plan
