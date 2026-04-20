from pydantic import BaseModel, Field
from typing import List
from datetime import date

class ExercisePrescription(BaseModel):
    exercise_name: str
    target_sets: int
    target_reps: str = Field(..., description="Range de repetições (ex: '8-12')")
    target_rpe: int = Field(..., ge=1, le=10)
    rest_seconds: int

class WorkoutSession(BaseModel):
    session_name: str
    day_of_week: int = Field(..., ge=1, le=7, description="Dia do microciclo (1-7)")
    exercises: List[ExercisePrescription]

class MicrocycleSchema(BaseModel):
    """Arquitetura das semanas de treino adaptadas, incorporando metadados importantes ligados a limites de segurança."""
    user_id: str
    start_date: date
    end_date: date
    workouts: List[WorkoutSession]
    ai_justification: str = Field(..., description="Justificativa gerada pela IA para as adaptações do estímulo de treino")
    
    # Metadados de Segurança
    max_weekly_sets_per_muscle: int = Field(..., description="Safety cap: Volume máximo (séries) por grupo muscular na semana")
    max_rpe_cap: int = Field(10, le=10, description="Safety cap: RPE máximo permitido no microciclo atual para evitar overtraining")
