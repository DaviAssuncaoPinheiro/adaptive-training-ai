"""
Validador de Seguranca (Safety Caps)

Aplica regras de seguranca pos-geracao da IA para garantir que o microciclo
prescrito nao exceda os limites fisiologicos seguros do praticante.

Regras implementadas:
    1. Limite de volume semanal por grupo muscular (varia por nivel).
    2. Deload automatico quando o readiness_score estiver criticamente baixo.
    3. Ajuste dinamico do RPE cap baseado na qualidade do sono e estresse.
    4. Clamping de sets e RPE por exercicio para respeitar os caps.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Limites de volume semanal por grupo muscular (sets) conforme nivel
# Baseado em diretrizes de periodizacao (Schoenfeld et al., Israetel MRV/MAV)
# ---------------------------------------------------------------------------
VOLUME_CAPS_BY_LEVEL: dict[str, int] = {
    "beginner": 12,
    "intermediate": 18,
    "advanced": 25,
}

# ---------------------------------------------------------------------------
# Limiares de prontidao e fadiga
# ---------------------------------------------------------------------------
DELOAD_READINESS_THRESHOLD = 40      # Abaixo disso, forcar deload
REDUCED_LOAD_READINESS_THRESHOLD = 55  # Entre 40-55, reduzir volume em 30%
DELOAD_VOLUME_REDUCTION = 0.50       # Deload reduz volume em 50%
REDUCED_VOLUME_FACTOR = 0.70         # Carga reduzida: 70% do volume

# RPE ajustes por qualidade de sono/estresse
LOW_SLEEP_THRESHOLD = 4              # Qualidade de sono <=4 (escala 1-10)
HIGH_STRESS_THRESHOLD = 7            # Estresse >=7 (escala 1-10)
RPE_REDUCTION_PER_FLAG = 1           # Reduz RPE cap em 1 por flag ativo


# ---------------------------------------------------------------------------
# 1. Calcular limites dinamicos
# ---------------------------------------------------------------------------

def compute_dynamic_caps(
    fitness_level: str,
    readiness_score: float | None,
    recent_sleep: float | None,
    recent_stress: float | None,
) -> dict[str, Any]:
    """
    Calcula os limites de seguranca dinamicos para o microciclo.

    Retorna:
        max_weekly_sets_per_muscle: teto de series por grupo muscular
        max_rpe_cap: RPE maximo permitido
        is_deload: se o microciclo deve ser de deload
        volume_factor: fator multiplicador do volume (1.0 = normal)
        flags: lista de motivos para ajustes aplicados
    """
    base_sets = VOLUME_CAPS_BY_LEVEL.get(fitness_level, VOLUME_CAPS_BY_LEVEL["intermediate"])
    max_rpe_cap = 10
    is_deload = False
    volume_factor = 1.0
    flags: list[str] = []

    # Regra 1: Deload por readiness critico
    if readiness_score is not None and readiness_score < DELOAD_READINESS_THRESHOLD:
        is_deload = True
        volume_factor = DELOAD_VOLUME_REDUCTION
        max_rpe_cap = 6
        flags.append(
            f"DELOAD FORCADO: readiness_score={readiness_score:.1f} "
            f"(abaixo do limiar de {DELOAD_READINESS_THRESHOLD})"
        )

    # Regra 2: Reducao de volume por readiness moderadamente baixo
    elif readiness_score is not None and readiness_score < REDUCED_LOAD_READINESS_THRESHOLD:
        volume_factor = REDUCED_VOLUME_FACTOR
        max_rpe_cap = 8
        flags.append(
            f"VOLUME REDUZIDO: readiness_score={readiness_score:.1f} "
            f"(abaixo do limiar moderado de {REDUCED_LOAD_READINESS_THRESHOLD})"
        )

    # Regra 3: Ajuste de RPE por sono ruim
    if recent_sleep is not None and recent_sleep <= LOW_SLEEP_THRESHOLD:
        max_rpe_cap = max(5, max_rpe_cap - RPE_REDUCTION_PER_FLAG)
        flags.append(
            f"RPE REDUZIDO (sono): qualidade_sono={recent_sleep:.1f} "
            f"(abaixo de {LOW_SLEEP_THRESHOLD})"
        )

    # Regra 4: Ajuste de RPE por estresse alto
    if recent_stress is not None and recent_stress >= HIGH_STRESS_THRESHOLD:
        max_rpe_cap = max(5, max_rpe_cap - RPE_REDUCTION_PER_FLAG)
        flags.append(
            f"RPE REDUZIDO (estresse): estresse={recent_stress:.1f} "
            f"(acima de {HIGH_STRESS_THRESHOLD})"
        )

    adjusted_sets = max(4, int(base_sets * volume_factor))

    return {
        "max_weekly_sets_per_muscle": adjusted_sets,
        "max_rpe_cap": max_rpe_cap,
        "is_deload": is_deload,
        "volume_factor": volume_factor,
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# 2. Aplicar caps ao microciclo gerado
# ---------------------------------------------------------------------------

def enforce_safety_caps(microcycle: dict, caps: dict) -> dict:
    """
    Aplica os limites de seguranca ao microciclo gerado pela IA.
    Modifica o microciclo in-place e retorna-o com os ajustes.

    Acoes:
        - Reduz RPE de exercicios que excedam o max_rpe_cap.
        - Reduz number de sets de exercicios se o volume total exceder o cap.
        - Atualiza os metadados de seguranca do microciclo.
        - Adiciona nota de seguranca na justificativa.
    """
    max_rpe = caps["max_rpe_cap"]
    max_sets = caps["max_weekly_sets_per_muscle"]
    is_deload = caps["is_deload"]
    flags = caps["flags"]

    adjustments_made: list[str] = []
    workouts = microcycle.get("workouts", [])

    # Contar sets por exercicio (proxy para grupo muscular)
    exercise_set_count: dict[str, int] = {}
    for workout in workouts:
        for ex in workout.get("exercises", []):
            name = ex.get("exercise_name", "")
            sets = ex.get("target_sets", 0)
            exercise_set_count[name] = exercise_set_count.get(name, 0) + sets

    for workout in workouts:
        for ex in workout.get("exercises", []):
            name = ex.get("exercise_name", "")

            # Clamp RPE
            current_rpe = ex.get("target_rpe", 7)
            if current_rpe > max_rpe:
                adjustments_made.append(
                    f"{name}: RPE reduzido de {current_rpe} para {max_rpe}"
                )
                ex["target_rpe"] = max_rpe

            # Clamp sets se volume total do exercicio exceder o cap
            total_sets = exercise_set_count.get(name, 0)
            current_sets = ex.get("target_sets", 3)
            if total_sets > max_sets and current_sets > 2:
                # Calcular fator de reducao proporcional
                reduction_factor = max_sets / total_sets
                new_sets = max(2, int(current_sets * reduction_factor))
                if new_sets < current_sets:
                    adjustments_made.append(
                        f"{name}: sets reduzidos de {current_sets} para {new_sets} "
                        f"(cap de {max_sets} sets/semana)"
                    )
                    ex["target_sets"] = new_sets

            # Em deload, aumentar descanso
            if is_deload:
                current_rest = ex.get("rest_seconds", 90)
                ex["rest_seconds"] = max(current_rest, 120)

    # Atualizar metadados de seguranca
    microcycle["max_weekly_sets_per_muscle"] = max_sets
    microcycle["max_rpe_cap"] = max_rpe

    # Anexar informacoes de seguranca a justificativa
    if flags or adjustments_made:
        safety_note = "\n\n[VALIDACAO DE SEGURANCA]"
        if flags:
            safety_note += "\nRegras ativadas:\n" + "\n".join(f"- {f}" for f in flags)
        if adjustments_made:
            safety_note += "\nAjustes aplicados:\n" + "\n".join(f"- {a}" for a in adjustments_made)

        microcycle["ai_justification"] = microcycle.get("ai_justification", "") + safety_note

    logger.info(
        "Safety caps aplicados: is_deload=%s, max_rpe=%d, max_sets=%d, ajustes=%d",
        is_deload, max_rpe, max_sets, len(adjustments_made),
    )

    return microcycle


# ---------------------------------------------------------------------------
# 3. Funcao de orquestracao
# ---------------------------------------------------------------------------

def validate_and_enforce(
    microcycle: dict,
    fitness_level: str,
    fatigue_analysis: dict,
) -> dict:
    """
    Funcao principal do validador de seguranca.
    Chamada pelo router de microciclo APOS a geracao pela IA e ANTES da persistencia.

    Params:
        microcycle: dict gerado pelo LLM Service
        fitness_level: nivel do praticante ('beginner', 'intermediate', 'advanced')
        fatigue_analysis: analise de fadiga do State Engine

    Returns:
        microcycle ajustado com caps de seguranca aplicados
    """
    readiness = fatigue_analysis.get("readiness_score")
    recent_avg = fatigue_analysis.get("recent_avg", {})
    recent_sleep = recent_avg.get("sleep_quality")
    recent_stress = recent_avg.get("stress_level")

    caps = compute_dynamic_caps(
        fitness_level=fitness_level,
        readiness_score=readiness,
        recent_sleep=recent_sleep,
        recent_stress=recent_stress,
    )

    logger.info(
        "Caps calculados para nivel=%s: max_sets=%d, max_rpe=%d, deload=%s, flags=%d",
        fitness_level, caps["max_weekly_sets_per_muscle"], caps["max_rpe_cap"],
        caps["is_deload"], len(caps["flags"]),
    )

    return enforce_safety_caps(microcycle, caps)
