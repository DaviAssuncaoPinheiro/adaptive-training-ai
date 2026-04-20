from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SetLog(BaseModel):
    exercise_name: str
    reps: int = Field(..., ge=0)
    weight_kg: float = Field(..., ge=0)
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Percepção Subjetiva de Esforço (RPE) - 1 a 10")

class WorkoutLogSchema(BaseModel):
    """Entidade para persistência unificada de registros da sessão executada."""
    user_id: str
    session_date: datetime
    workout_name: str
    duration_minutes: int = Field(..., gt=0, description="Duração do treino em minutos")
    sets: List[SetLog] = Field(default_factory=list, description="Séries executadas na sessão")
    notes: Optional[str] = Field(None, description="Observações opcionais do praticante")
