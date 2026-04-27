"""
Schemas de response para o endpoint de estado do praticante.
Estrutura o retorno do State Engine em modelos Pydantic tipados.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import date


class PeriodInfo(BaseModel):
    """Janelas temporais usadas nos calculos."""
    recent_window_days: int
    baseline_window_days: int


class ExerciseVolume(BaseModel):
    """Metricas de volume para um exercicio individual."""
    sets: int
    tonnage: float
    avg_rpe: Optional[float] = None


class VolumeMetrics(BaseModel):
    """Metricas consolidadas de volume e intensidade."""
    total_sets: int = Field(..., description="Total de series realizadas no periodo")
    total_tonnage: float = Field(..., description="Tonelagem total (reps x carga) em kg")
    avg_rpe: Optional[float] = Field(None, description="RPE medio ponderado")
    sessions_count: int = Field(..., description="Numero de sessoes registradas")
    avg_duration_minutes: float = Field(..., description="Duracao media por sessao em minutos")
    volume_per_exercise: Dict[str, ExerciseVolume] = Field(
        default_factory=dict,
        description="Volume detalhado por exercicio",
    )


class FatigueAnalysis(BaseModel):
    """Analise de fadiga acumulada: comparativo recente vs baseline."""
    recent_avg: Dict[str, float] = Field(
        default_factory=dict,
        description="Media de cada metrica nos ultimos 7 dias",
    )
    baseline_avg: Dict[str, float] = Field(
        default_factory=dict,
        description="Media de cada metrica nos ultimos 30 dias",
    )
    delta: Dict[str, float] = Field(
        default_factory=dict,
        description="Diferenca (recente - baseline). Positivo em fadiga = pior.",
    )
    readiness_score: Optional[float] = Field(
        None,
        description="Score consolidado de prontidao (0-100). Quanto maior, melhor.",
    )
    data_points_recent: int = Field(0, description="Quantidade de check-ins nos ultimos 7 dias")
    data_points_baseline: int = Field(0, description="Quantidade de check-ins nos ultimos 30 dias")


class AdherenceMetrics(BaseModel):
    """Indice de adesao ao microciclo prescrito."""
    prescribed_sessions: int = Field(..., description="Sessoes prescritas no microciclo")
    completed_sessions: int = Field(..., description="Sessoes efetivamente realizadas")
    adherence_rate: Optional[float] = Field(
        None,
        description="Taxa de adesao (0.0 a 1.0). Ex: 0.75 = 75%",
    )
    detail: Optional[str] = Field(None, description="Observacao adicional")


class ExerciseTolerance(BaseModel):
    """Analise de volume tolerado para um exercicio individual."""
    total_sets_in_period: int
    avg_rpe: Optional[float] = None
    avg_weight_kg: Optional[float] = None
    trend: str = Field(..., description="Tendencia: 'stable', 'improving' ou 'degrading'")


class PractitionerStateResponse(BaseModel):
    """
    Response completa do endpoint de estado do praticante.
    Consolida todas as metricas calculadas pelo State Engine.
    Consumido pelo modulo de IA na Fase 3 para geracao de microciclos.
    """
    user_id: str
    generated_at: date
    period: PeriodInfo
    weekly_volume: VolumeMetrics
    monthly_volume: VolumeMetrics
    fatigue_analysis: FatigueAnalysis
    adherence: AdherenceMetrics
    tolerated_volume: Dict[str, ExerciseTolerance] = Field(
        default_factory=dict,
        description="Analise de volume tolerado por exercicio",
    )
