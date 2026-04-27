"""
Schemas de request/response para o endpoint de geracao de microciclos.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class GenerateMicrocycleRequest(BaseModel):
    """
    Payload para solicitar a geracao de um novo microciclo.
    O user_id e suficiente — o perfil e o estado sao buscados internamente.
    """
    user_id: str = Field(..., description="UUID do usuario autenticado no Supabase Auth")


# ---------------------------------------------------------------------------
# Response — reutiliza a estrutura do dominio mas com campos extras
# ---------------------------------------------------------------------------

class ExercisePrescriptionResponse(BaseModel):
    """Exercicio prescrito pela IA."""
    exercise_name: str
    target_sets: int
    target_reps: str
    target_rpe: int
    rest_seconds: int


class WorkoutSessionResponse(BaseModel):
    """Sessao de treino prescrita pela IA."""
    session_name: str
    day_of_week: int
    exercises: List[ExercisePrescriptionResponse]


class MicrocycleResponse(BaseModel):
    """
    Microciclo gerado e persistido.
    Inclui metadados do banco (id, created_at) alem da prescricao.
    """
    id: int
    user_id: str
    start_date: date
    end_date: date
    workouts: List[WorkoutSessionResponse]
    ai_justification: str
    max_weekly_sets_per_muscle: int
    max_rpe_cap: int
    created_at: datetime


class GenerationStatusResponse(BaseModel):
    """
    Response completa do endpoint de geracao.
    Inclui o microciclo gerado e metadados de debug.
    """
    status: str = Field(..., description="'success' ou 'error'")
    microcycle: Optional[MicrocycleResponse] = None
    message: Optional[str] = Field(None, description="Mensagem descritiva do resultado")
