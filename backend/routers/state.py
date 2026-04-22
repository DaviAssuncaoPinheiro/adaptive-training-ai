"""
Rota de estado do praticante.
Consolida todas as metricas do State Engine em um unico endpoint.
"""

from fastapi import APIRouter, HTTPException

from backend.services.state_engine import build_practitioner_state
from backend.schemas.state_models import PractitionerStateResponse

router = APIRouter(prefix="/state", tags=["State Engine"])


@router.get("/{user_id}", response_model=PractitionerStateResponse)
async def get_practitioner_state(user_id: str):
    """
    Retorna o estado consolidado do praticante.

    Calcula em tempo real:
    - Volume semanal e mensal (sets, tonelagem, RPE medio)
    - Fadiga acumulada (comparativo 7d vs 30d + readiness score)
    - Indice de adesao (sessoes realizadas vs prescritas)
    - Volume tolerado por exercicio (deteccao de tendencia)

    Este report e a entrada principal para o gerador de microciclos (Fase 3).
    """
    try:
        state = build_practitioner_state(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular estado do praticante: {str(e)}",
        )

    return PractitionerStateResponse(**state)
