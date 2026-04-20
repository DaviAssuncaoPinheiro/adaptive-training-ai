from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from enum import Enum

class FitnessLevel(str, Enum):
    beginner = 'beginner'
    intermediate = 'intermediate'
    advanced = 'advanced'

class Goal(str, Enum):
    hypertrophy = 'hypertrophy'
    strength = 'strength'
    endurance = 'endurance'
    weight_loss = 'weight_loss'

class UserSchema(BaseModel):
    """Schema para coletar e validar dados demográficos e do perfil base durante o Onboarding."""
    user_id: str = Field(..., description="UUID from Supabase Auth")
    age: int = Field(..., gt=0, description="Idade do praticante")
    weight_kg: float = Field(..., gt=0, description="Peso corporal em kg")
    height_cm: float = Field(..., gt=0, description="Altura em cm")
    fitness_level: FitnessLevel = Field(..., description="Nível de condicionamento atual")
    primary_goal: Goal = Field(..., description="Objetivo principal do treino")
    available_equipment: List[str] = Field(default_factory=list, description="Lista de equipamentos disponíveis")
    created_at: datetime = Field(default_factory=datetime.utcnow)
