"""
Rotas de perfil do praticante.
Endpoints para criacao, leitura e atualizacao do perfil vinculado ao user_id
do Supabase Auth.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from backend.database import get_supabase_client
from backend.schemas.api_models import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_user_id(authorization: str) -> str:
    """
    Extrai e valida o user_id a partir do token JWT do Supabase.
    Em producao, decodificar o JWT com a chave publica do Supabase.
    Por simplicidade nesta fase, recebemos o user_id via header customizado.
    """
    return authorization


# ---------------------------------------------------------------------------
# GET /profiles/{user_id}
# ---------------------------------------------------------------------------
@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """Retorna o perfil completo de um praticante pelo user_id."""
    supabase = get_supabase_client()

    response = (
        supabase
        .table("profiles")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    data = getattr(response, "data", None) if response else None
    if data is None:
        raise HTTPException(status_code=404, detail="Perfil nao encontrado")

    return ProfileResponse(**data)


# ---------------------------------------------------------------------------
# POST /profiles
# ---------------------------------------------------------------------------
@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(
    payload: ProfileCreateRequest,
    x_user_id: str = Header(..., description="UUID do usuario autenticado no Supabase Auth"),
):
    """
    Cria um novo perfil para o praticante.
    Se o perfil ja existir, realiza upsert (atualiza os dados).
    O user_id e recebido via header X-User-Id.
    """
    supabase = get_supabase_client()

    row = {
        "user_id": x_user_id,
        "age": payload.age,
        "weight_kg": payload.weight_kg,
        "height_cm": payload.height_cm,
        "fitness_level": payload.fitness_level.value,
        "primary_goal": payload.primary_goal.value,
        "available_equipment": payload.available_equipment,
    }

    response = (
        supabase
        .table("profiles")
        .upsert(row, on_conflict="user_id")
        .execute()
    )

    data = getattr(response, "data", []) or [] if response else []
    if not data:
        raise HTTPException(status_code=500, detail="Falha ao criar perfil")

    return ProfileResponse(**data[0])


# ---------------------------------------------------------------------------
# PUT /profiles/{user_id}
# ---------------------------------------------------------------------------
@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(user_id: str, payload: ProfileUpdateRequest):
    """
    Atualiza parcialmente o perfil do praticante.
    Apenas os campos presentes no payload sao atualizados.
    """
    supabase = get_supabase_client()

    update_data = payload.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    # Converter enums para string
    if "fitness_level" in update_data:
        update_data["fitness_level"] = update_data["fitness_level"].value
    if "primary_goal" in update_data:
        update_data["primary_goal"] = update_data["primary_goal"].value

    response = (
        supabase
        .table("profiles")
        .update(update_data)
        .eq("user_id", user_id)
        .execute()
    )

    data = getattr(response, "data", []) or [] if response else []
    if not data:
        raise HTTPException(status_code=404, detail="Perfil nao encontrado para atualizar")

    return ProfileResponse(**data[0])
