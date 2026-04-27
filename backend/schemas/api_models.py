"""
Schemas de request/response especificos para a API de perfis.
Separa o contrato de API (o que o endpoint recebe/devolve) do contrato de
dominio (UserSchema), permitindo evolucao independente.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.schemas.user import FitnessLevel, Goal


# ---------------------------------------------------------------------------
# Request: criacao/atualizacao de perfil
# ---------------------------------------------------------------------------
class ProfileCreateRequest(BaseModel):
    """Payload recebido pelo endpoint de criacao de perfil."""
    age: int = Field(..., gt=0, description="Idade do praticante")
    weight_kg: float = Field(..., gt=0, description="Peso corporal em kg")
    height_cm: float = Field(..., gt=0, description="Altura em cm")
    fitness_level: FitnessLevel
    primary_goal: Goal
    available_equipment: List[str] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    """Payload para atualizacao parcial do perfil. Todos os campos sao opcionais."""
    age: Optional[int] = Field(None, gt=0)
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    fitness_level: Optional[FitnessLevel] = None
    primary_goal: Optional[Goal] = None
    available_equipment: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Response: perfil retornado pela API
# ---------------------------------------------------------------------------
class ProfileResponse(BaseModel):
    """Representacao do perfil retornada ao cliente."""
    id: int
    user_id: str
    age: int
    weight_kg: float
    height_cm: float
    fitness_level: str
    primary_goal: str
    available_equipment: List[str]
    created_at: datetime
    updated_at: datetime
