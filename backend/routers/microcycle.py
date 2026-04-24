"""
Rota de geracao de microciclos via IA.

Orquestra o fluxo completo:
    1. Busca o perfil do praticante.
    2. Calcula o estado consolidado via State Engine.
    3. Gera o microciclo via LLM (Ollama).
    3.5. Aplica validacao de seguranca (Safety Caps).
    4. Persiste o resultado no banco.
    5. Retorna o microciclo ao cliente.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.database import get_supabase_client
from backend.services.state_engine import build_practitioner_state
from backend.services.llm_service import generate_microcycle, persist_microcycle, OllamaClient
from backend.services.safety_validator import validate_and_enforce
from backend.schemas.microcycle_models import (
    GenerateMicrocycleRequest,
    GenerationStatusResponse,
    MicrocycleResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/microcycle", tags=["Microcycle Generation"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_profile(user_id: str) -> dict:
    """Busca o perfil do praticante no banco. Levanta 404 se nao encontrado."""
    supabase = get_supabase_client()
    response = (
        supabase
        .table("profiles")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response.data is None:
        raise HTTPException(
            status_code=404,
            detail="Perfil do praticante nao encontrado. Complete o onboarding antes de gerar um microciclo.",
        )
    return response.data


# ---------------------------------------------------------------------------
# POST /microcycle/generate
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerationStatusResponse,
    status_code=201,
    summary="Gera um novo microciclo adaptativo via IA",
)
async def generate_microcycle_endpoint(payload: GenerateMicrocycleRequest):
    """
    Endpoint principal de geracao de microciclos.

    Fluxo:
    1. Valida que o praticante possui perfil (onboarding completo).
    2. Calcula o estado atual via State Engine (volume, fadiga, adesao).
    3. Envia os dados ao LLM (Ollama) para geracao da prescricao.
    3.5. Aplica validacao de seguranca (Safety Caps) pos-geracao.
    4. Persiste o microciclo validado no banco.
    5. Retorna o microciclo ao frontend.

    Requer que o servico Ollama esteja rodando via Docker.
    """
    user_id = payload.user_id

    # 1. Buscar perfil
    profile = _fetch_profile(user_id)
    logger.info("Perfil carregado para user_id=%s (nivel=%s, objetivo=%s)",
                user_id, profile.get("fitness_level"), profile.get("primary_goal"))

    # 2. Calcular estado via State Engine
    try:
        state = build_practitioner_state(user_id)
    except Exception as e:
        logger.error("Erro ao calcular estado para user_id=%s: %s", user_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular estado do praticante: {str(e)}",
        )

    # 3. Gerar microciclo via LLM
    try:
        microcycle_data = await generate_microcycle(
            user_id=user_id,
            profile=profile,
            state=state,
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 3.5. Aplicar validacao de seguranca (Safety Caps)
    fatigue_analysis = state.get("fatigue_analysis", {})
    fitness_level = profile.get("fitness_level", "intermediate")
    microcycle_data = validate_and_enforce(
        microcycle=microcycle_data,
        fitness_level=fitness_level,
        fatigue_analysis=fatigue_analysis,
    )
    logger.info("Safety caps aplicados para user_id=%s", user_id)

    # 4. Persistir no banco
    try:
        persisted = persist_microcycle(microcycle_data)
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Microciclo gerado mas falha ao persistir: {str(e)}",
        )

    # 5. Retornar
    # O campo workouts pode vir como string JSON do banco — normalizar
    workouts = persisted.get("workouts", [])
    if isinstance(workouts, str):
        import json
        workouts = json.loads(workouts)

    microcycle_response = MicrocycleResponse(
        id=persisted["id"],
        user_id=persisted["user_id"],
        start_date=persisted["start_date"],
        end_date=persisted["end_date"],
        workouts=workouts,
        ai_justification=persisted["ai_justification"],
        max_weekly_sets_per_muscle=persisted["max_weekly_sets_per_muscle"],
        max_rpe_cap=persisted["max_rpe_cap"],
        created_at=persisted["created_at"],
    )

    return GenerationStatusResponse(
        status="success",
        microcycle=microcycle_response,
        message=f"Microciclo gerado com {len(workouts)} sessoes para o periodo "
                f"{persisted['start_date']} a {persisted['end_date']}.",
    )


# ---------------------------------------------------------------------------
# GET /microcycle/health — verifica se o Ollama esta acessivel
# ---------------------------------------------------------------------------

@router.get("/health", summary="Verifica conectividade com o servico Ollama")
async def check_ollama_health():
    """Retorna o status de conectividade com o servico Ollama."""
    ollama = OllamaClient()
    is_healthy = await ollama.check_health()

    if is_healthy:
        return {
            "status": "ok",
            "ollama_url": ollama.base_url,
            "model": ollama.model,
        }

    return {
        "status": "unavailable",
        "ollama_url": ollama.base_url,
        "model": ollama.model,
        "detail": "Servico Ollama nao esta acessivel. Execute 'docker compose up -d'.",
    }
