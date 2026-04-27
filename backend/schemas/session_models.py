"""
Schemas de request/response para os endpoints de sessao (workout logs),
check-ins e consulta de historico.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Workout Log — Request / Response
# ---------------------------------------------------------------------------

class SetLogRequest(BaseModel):
    """Uma serie executada pelo praticante."""
    exercise_name: str = Field(..., description="Nome do exercicio")
    reps: int = Field(..., ge=0, description="Repeticoes realizadas")
    weight_kg: float = Field(..., ge=0, description="Carga em kg")
    rpe: Optional[int] = Field(None, ge=1, le=10, description="RPE (1-10)")


class WorkoutLogCreateRequest(BaseModel):
    """Payload para registrar uma sessao de treino executada."""
    user_id: str = Field(..., description="UUID do usuario")
    session_date: datetime = Field(..., description="Data e hora da sessao")
    workout_name: str = Field(..., description="Nome do treino (ex: Treino A)")
    duration_minutes: int = Field(..., gt=0, description="Duracao em minutos")
    sets: List[SetLogRequest] = Field(default_factory=list, description="Series executadas")
    notes: Optional[str] = Field(None, description="Observacoes do praticante")


class SetLogResponse(BaseModel):
    """Serie retornada pela API."""
    exercise_name: str
    reps: int
    weight_kg: float
    rpe: Optional[int] = None


class WorkoutLogResponse(BaseModel):
    """Sessao de treino retornada pela API."""
    id: int
    user_id: str
    session_date: datetime
    workout_name: str
    duration_minutes: int
    sets: List[SetLogResponse]
    notes: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Check-In — Request / Response
# ---------------------------------------------------------------------------

class CheckInCreateRequest(BaseModel):
    """Payload para registrar um check-in diario de prontidao."""
    user_id: str = Field(..., description="UUID do usuario")
    check_in_date: date = Field(..., description="Data do check-in")
    sleep_quality: int = Field(..., ge=1, le=10, description="Qualidade do sono (1-10)")
    energy_level: int = Field(..., ge=1, le=10, description="Nivel de energia (1-10)")
    muscle_soreness: int = Field(..., ge=1, le=10, description="Dor muscular (1=nenhuma, 10=extrema)")
    stress_level: int = Field(..., ge=1, le=10, description="Estresse (1-10)")
    fatigue_level: int = Field(..., ge=1, le=10, description="Fadiga central (1-10)")


class CheckInResponse(BaseModel):
    """Check-in retornado pela API."""
    id: int
    user_id: str
    check_in_date: date
    sleep_quality: int
    energy_level: int
    muscle_soreness: int
    stress_level: int
    fatigue_level: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Historico — Response
# ---------------------------------------------------------------------------

class ExerciseProgressEntry(BaseModel):
    """Ponto de dados para evolucao de carga de um exercicio."""
    session_date: datetime
    workout_name: str
    total_sets: int
    total_reps: int
    max_weight_kg: float
    avg_rpe: Optional[float] = None


class ExerciseProgressResponse(BaseModel):
    """Historico de evolucao de carga para um exercicio especifico."""
    exercise_name: str
    entries: List[ExerciseProgressEntry]
    total_sessions: int


class WorkoutHistoryResponse(BaseModel):
    """Resumo do historico de treino do praticante."""
    user_id: str
    total_sessions: int
    date_range: Optional[dict] = Field(None, description="{'from': date, 'to': date}")
    sessions: List[WorkoutLogResponse]
