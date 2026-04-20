from pydantic import BaseModel, Field
from datetime import date

class CheckInSchema(BaseModel):
    """Estrutura que capta percepções pré/pós-treino de prontidão, descanso, recuperação e fadiga central."""
    user_id: str
    check_in_date: date
    sleep_quality: int = Field(..., ge=1, le=10, description="Qualidade do sono (1=ruim, 10=excelente)")
    energy_level: int = Field(..., ge=1, le=10, description="Nível de prontidão/energia (1-10)")
    muscle_soreness: int = Field(..., ge=1, le=10, description="Nível de dor muscular tardia (1-10, onde 10 é dor extrema)")
    stress_level: int = Field(..., ge=1, le=10, description="Nível de estresse sistêmico (1-10)")
    fatigue_level: int = Field(..., ge=1, le=10, description="Percepção de fadiga central (1-10)")
