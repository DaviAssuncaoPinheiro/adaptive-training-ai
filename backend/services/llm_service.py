"""
Servico de integracao com o Ollama e geracao de microciclos via LLM.

Responsabilidades:
    1. Comunicacao assincrona com a API REST do Ollama.
    2. Construcao de prompts contextualizados com o perfil e estado do praticante.
    3. Parsing e validacao do JSON retornado pelo LLM contra o schema do microciclo.
    4. Mecanismo de retry com fallback para saidas malformadas.
"""

import json
import logging
import re
from datetime import date, timedelta
from typing import Any

import httpx

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
OLLAMA_GENERATE_ENDPOINT = "/api/generate"
LLM_TEMPERATURE = 0.7
LLM_MAX_RETRIES = 2
LLM_TIMEOUT_SECONDS = 120


# ---------------------------------------------------------------------------
# 1. Cliente Ollama
# ---------------------------------------------------------------------------

class OllamaClient:
    """
    Cliente HTTP assincrono para a API do Ollama.
    Encapsula a comunicacao de rede e o tratamento de erros de conexao.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = LLM_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str, system: str = "") -> str:
        """
        Envia um prompt ao Ollama e retorna a resposta completa como string.
        Usa o modo stream=false para receber a resposta de uma vez.
        """
        url = f"{self.base_url}{OLLAMA_GENERATE_ENDPOINT}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": LLM_TEMPERATURE,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
            except httpx.ConnectError:
                raise ConnectionError(
                    f"Nao foi possivel conectar ao Ollama em {self.base_url}. "
                    "Verifique se o servico esta rodando via 'docker compose up -d'."
                )
            except httpx.TimeoutException:
                raise TimeoutError(
                    f"Timeout de {self.timeout}s excedido ao aguardar resposta do Ollama. "
                    "Considere aumentar LLM_TIMEOUT_SECONDS ou usar um modelo menor."
                )
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"Ollama retornou status {e.response.status_code}: {e.response.text}"
                )

    async def check_health(self) -> bool:
        """Verifica se o servico Ollama esta acessivel."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self.base_url)
                return response.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 2. Gerador de Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Voce e um personal trainer especialista em periodizacao de treinos.
Sua tarefa e gerar um microciclo semanal de treino personalizado com base no perfil
e no estado atual do praticante.

REGRAS OBRIGATORIAS:
1. Responda EXCLUSIVAMENTE com um objeto JSON valido. Nenhum texto antes ou depois.
2. O JSON deve seguir EXATAMENTE a estrutura abaixo.
3. Adapte volume, intensidade e selecao de exercicios ao nivel do praticante.
4. Considere a fadiga acumulada e o readiness_score para modular a carga.
5. Se o readiness_score for baixo (< 40), prescreva uma semana de deload.
6. Respeite os equipamentos disponiveis ao selecionar exercicios.
7. Inclua uma justificativa detalhada explicando suas decisoes.

ESTRUTURA JSON OBRIGATORIA:
{
  "workouts": [
    {
      "session_name": "Nome da Sessao (ex: Treino A - Peito e Triceps)",
      "day_of_week": 1,
      "exercises": [
        {
          "exercise_name": "Nome do Exercicio",
          "target_sets": 3,
          "target_reps": "8-12",
          "target_rpe": 7,
          "rest_seconds": 90
        }
      ]
    }
  ],
  "ai_justification": "Explicacao detalhada das adaptacoes...",
  "max_weekly_sets_per_muscle": 16,
  "max_rpe_cap": 8
}"""


def build_user_prompt(profile: dict, state: dict) -> str:
    """
    Constroi o prompt do usuario com os dados do perfil e o estado consolidado.
    Formata as informacoes de maneira clara e estruturada para o LLM.
    """
    # Extrair dados do perfil
    age = profile.get("age", "N/A")
    weight = profile.get("weight_kg", "N/A")
    height = profile.get("height_cm", "N/A")
    level = profile.get("fitness_level", "N/A")
    goal = profile.get("primary_goal", "N/A")
    equipment = profile.get("available_equipment", [])
    equipment_str = ", ".join(equipment) if equipment else "Nenhum especificado"

    # Extrair metricas do estado (Fase 2)
    weekly = state.get("weekly_volume", {})
    fatigue = state.get("fatigue_analysis", {})
    adherence = state.get("adherence", {})
    tolerated = state.get("tolerated_volume", {})

    # Formatar tendencias de volume tolerado
    trends_lines = []
    for exercise, data in tolerated.items():
        trend = data.get("trend", "stable")
        avg_rpe = data.get("avg_rpe", "N/A")
        trends_lines.append(f"  - {exercise}: tendencia={trend}, RPE medio={avg_rpe}")
    trends_str = "\n".join(trends_lines) if trends_lines else "  Sem dados suficientes."

    prompt = f"""PERFIL DO PRATICANTE:
- Idade: {age} anos
- Peso: {weight} kg
- Altura: {height} cm
- Nivel: {level}
- Objetivo principal: {goal}
- Equipamentos disponiveis: {equipment_str}

ESTADO ATUAL (ultimos 7 dias):
- Sessoes realizadas: {weekly.get('sessions_count', 0)}
- Total de series: {weekly.get('total_sets', 0)}
- Tonelagem total: {weekly.get('total_tonnage', 0)} kg
- RPE medio: {weekly.get('avg_rpe', 'N/A')}
- Duracao media: {weekly.get('avg_duration_minutes', 0)} min

ANALISE DE FADIGA:
- Readiness Score: {fatigue.get('readiness_score', 'N/A')}/100
- Fadiga recente (delta): {json.dumps(fatigue.get('delta', {}), ensure_ascii=False)}

ADESAO AO ULTIMO MICROCICLO:
- Sessoes prescritas: {adherence.get('prescribed_sessions', 0)}
- Sessoes realizadas: {adherence.get('completed_sessions', 0)}
- Taxa de adesao: {adherence.get('adherence_rate', 'N/A')}

TENDENCIAS POR EXERCICIO:
{trends_str}

Com base nesses dados, gere um microciclo semanal otimizado. Responda APENAS com o JSON."""

    return prompt


# ---------------------------------------------------------------------------
# 3. Parser de Resposta do LLM
# ---------------------------------------------------------------------------

def extract_json_from_response(raw: str) -> dict:
    """
    Extrai e parseia o JSON da resposta do LLM.
    Trata casos comuns:
        - Resposta pura (JSON direto)
        - JSON envolto em blocos de markdown (```json ... ```)
        - Texto antes/depois do JSON
    """
    # Remover blocos de markdown
    cleaned = re.sub(r"```json\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()

    # Tentar parse direto
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Tentar encontrar o primeiro objeto JSON valido na string
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = cleaned[brace_start:brace_end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Nao foi possivel extrair JSON valido da resposta do LLM. "
        f"Resposta recebida (primeiros 500 chars): {raw[:500]}"
    )


def validate_microcycle_structure(data: dict) -> dict:
    """
    Valida que o dict extraido contem os campos obrigatorios do microciclo.
    Aplica defaults razoaveis para campos ausentes e normaliza a estrutura.
    """
    # Validar campo workouts
    workouts = data.get("workouts")
    if not workouts or not isinstance(workouts, list):
        raise ValueError("O campo 'workouts' esta ausente ou nao e uma lista.")

    validated_workouts = []
    for i, w in enumerate(workouts):
        if not isinstance(w, dict):
            continue

        exercises = w.get("exercises", [])
        validated_exercises = []
        for ex in exercises:
            if not isinstance(ex, dict):
                continue
            validated_exercises.append({
                "exercise_name": ex.get("exercise_name", f"Exercicio {len(validated_exercises) + 1}"),
                "target_sets": int(ex.get("target_sets", 3)),
                "target_reps": str(ex.get("target_reps", "8-12")),
                "target_rpe": max(1, min(10, int(ex.get("target_rpe", 7)))),
                "rest_seconds": int(ex.get("rest_seconds", 90)),
            })

        if validated_exercises:
            validated_workouts.append({
                "session_name": w.get("session_name", f"Sessao {i + 1}"),
                "day_of_week": max(1, min(7, int(w.get("day_of_week", i + 1)))),
                "exercises": validated_exercises,
            })

    if not validated_workouts:
        raise ValueError("Nenhuma sessao de treino valida foi encontrada na resposta do LLM.")

    # Validar justificativa
    justification = data.get("ai_justification", "")
    if not justification:
        justification = "Microciclo gerado automaticamente com base no estado atual do praticante."

    # Validar safety caps
    max_sets = data.get("max_weekly_sets_per_muscle")
    if max_sets is None or not isinstance(max_sets, (int, float)):
        max_sets = 20  # Default conservador

    max_rpe = data.get("max_rpe_cap")
    if max_rpe is None or not isinstance(max_rpe, (int, float)):
        max_rpe = 9  # Default conservador

    return {
        "workouts": validated_workouts,
        "ai_justification": justification,
        "max_weekly_sets_per_muscle": int(max_sets),
        "max_rpe_cap": max(1, min(10, int(max_rpe))),
    }


# ---------------------------------------------------------------------------
# 4. Orquestrador de Geracao
# ---------------------------------------------------------------------------

async def generate_microcycle(
    user_id: str,
    profile: dict,
    state: dict,
) -> dict:
    """
    Funcao principal de geracao de microciclo.

    Fluxo:
        1. Constroi o prompt com perfil + estado.
        2. Envia ao Ollama.
        3. Parseia e valida o JSON retornado.
        4. Adiciona metadados (user_id, datas).
        5. Retorna o microciclo pronto para persistencia.

    Implementa retry: em caso de resposta malformada, tenta novamente
    ate LLM_MAX_RETRIES vezes.
    """
    ollama = OllamaClient()
    user_prompt = build_user_prompt(profile, state)

    last_error = None
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        logger.info(
            "Gerando microciclo para user_id=%s (tentativa %d/%d)",
            user_id, attempt, LLM_MAX_RETRIES,
        )

        try:
            raw_response = await ollama.generate(
                prompt=user_prompt,
                system=SYSTEM_PROMPT,
            )

            parsed = extract_json_from_response(raw_response)
            validated = validate_microcycle_structure(parsed)

            # Calcular datas do microciclo (proxima segunda a domingo)
            today = date.today()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            start = today + timedelta(days=days_until_monday)
            end = start + timedelta(days=6)

            microcycle = {
                "user_id": user_id,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                **validated,
            }

            logger.info(
                "Microciclo gerado com sucesso para user_id=%s (%d sessoes)",
                user_id, len(validated["workouts"]),
            )
            return microcycle

        except (ValueError, KeyError, TypeError) as e:
            last_error = e
            logger.warning(
                "Tentativa %d falhou ao parsear resposta do LLM: %s",
                attempt, str(e),
            )
            continue

    raise RuntimeError(
        f"Falha ao gerar microciclo apos {LLM_MAX_RETRIES} tentativas. "
        f"Ultimo erro: {last_error}"
    )


# ---------------------------------------------------------------------------
# 5. Persistencia do Microciclo
# ---------------------------------------------------------------------------

def persist_microcycle(microcycle: dict) -> dict:
    """
    Persiste o microciclo gerado na tabela 'microcycles' do Supabase.
    Retorna o registro inserido com o ID gerado pelo banco.
    """
    from backend.database import get_supabase_client

    supabase = get_supabase_client()

    row = {
        "user_id": microcycle["user_id"],
        "start_date": microcycle["start_date"],
        "end_date": microcycle["end_date"],
        "workouts": json.dumps(microcycle["workouts"]),
        "ai_justification": microcycle["ai_justification"],
        "max_weekly_sets_per_muscle": microcycle["max_weekly_sets_per_muscle"],
        "max_rpe_cap": microcycle["max_rpe_cap"],
    }

    response = (
        supabase
        .table("microcycles")
        .insert(row)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Falha ao persistir microciclo no banco de dados.")

    return response.data[0]
