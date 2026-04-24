# DEV 2 — Documentacao Tecnica: Logica de Treino e Geracao de Microciclo

Este documento serve como guia tecnico para desenvolvedores sobre o estado atual da aplicacao **Adaptive Training AI**, um Micro SAAS para prescricao adaptativa de treinos utilizando Inteligencia Artificial hibrida. Aqui sao documentadas exclusivamente as alteracoes realizadas pelo DEV 2, responsavel pela persistencia de dados, logica de estado do praticante e geracao de microciclos.

---

## Contexto Anterior (Estado Antes do DEV 2)

O projeto possuia apenas:

- Um frontend funcional em Next.js 15 com autenticacao (Supabase Auth), onboarding wizard, dashboard, session logger e visualizacao de microciclo.
- Um diretorio `/backend/schemas/` contendo quatro contratos Pydantic de dominio (`user.py`, `workout_log.py`, `check_in.py`, `microcycle.py`).
- Um `requirements.txt` com apenas `pydantic>=2.0.0`.
- Um `docker-compose.yml` configurando o servico Ollama para inferencia local de LLMs.

O backend nao possuia servidor de aplicacao, conexao com banco de dados, endpoints HTTP nem logica de negocio. O frontend se comunicava diretamente com o Supabase via SDK JavaScript.

---

## Arquitetura Final (Apos Fases 1, 2, 3 e 4)

A Fase 1 introduziu uma camada de backend em Python com FastAPI como servidor de aplicacao. A arquitetura agora opera em tres camadas:

```
Frontend (Next.js 15)  <--->  Backend (FastAPI)  <--->  Supabase Cloud (PostgreSQL + Auth)
                                    |
                              Docker (Ollama) [previsto para Fase 3]
```

O frontend continua se comunicando diretamente com o Supabase para operacoes simples (auth, leituras diretas). O backend FastAPI e usado para operacoes que exigem logica de negocio, validacao avancada, orquestracao de IA e aplicacao de regras de seguranca.

Ambos acessam o mesmo banco PostgreSQL no Supabase. A diferenca esta nas credenciais:

- **Frontend**: usa a `anon key` com Row Level Security (RLS) ativo.
- **Backend**: usa a `service_role key`, que bypassa RLS quando necessario para operacoes administrativas.

---

## Estrutura de Arquivos Criados

```
backend/
  __init__.py                  # Pacote raiz do backend
  main.py                      # Entrypoint do FastAPI
  config.py                    # Carregamento de variaveis de ambiente
  database.py                  # Factory do cliente Supabase
  requirements.txt             # Dependencias Python (atualizado)
  .env.example                 # Template de configuracao

  db/
    __init__.py
    schema.sql                 # Migracao SQL completa para Supabase

  routers/
    __init__.py
    profiles.py                # Endpoints CRUD de perfil
    state.py                   # Endpoint de estado do praticante [FASE 2]
    microcycle.py              # Endpoint de geracao de microciclo [FASE 3, atualizado FASE 4]
    sessions.py                # Endpoints de sessao, check-in e historico [FASE 4]

  schemas/
    __init__.py                # (pre-existente)
    user.py                    # (pre-existente)
    workout_log.py             # (pre-existente)
    check_in.py                # (pre-existente)
    microcycle.py              # (pre-existente)
    api_models.py              # DTOs de request/response da API
    state_models.py            # DTOs de response do State Engine [FASE 2]
    microcycle_models.py       # DTOs de request/response da geracao [FASE 3]
    session_models.py          # DTOs de sessao, check-in e historico [FASE 4]

  services/
    __init__.py
    state_engine.py            # Motor de analise de estado [FASE 2]
    llm_service.py             # Integracao com Ollama e geracao [FASE 3]
    safety_validator.py        # Validador de seguranca (Safety Caps) [FASE 4]

  tests/
    test_parser.py             # Teste do parser de JSON do LLM [FASE 3]
```

---

## Detalhamento dos Modulos Implementados

### 1. Migracao SQL (`backend/db/schema.sql`)

Script unico para execucao no SQL Editor do Supabase Dashboard. Cria toda a infraestrutura de persistencia.

**Tabelas criadas:**

| Tabela | Descricao | Schema de Origem |
|---|---|---|
| `profiles` | Dados demograficos e preferencias do praticante | `user.py` |
| `workout_logs` | Registro completo de sessoes de treino executadas | `workout_log.py` |
| `check_ins` | Metricas subjetivas diarias de prontidao (sono, fadiga, estresse, dor, energia) | `check_in.py` |
| `microcycles` | Planos semanais de treino gerados pela IA, com safety caps | `microcycle.py` |

**Decisoes tecnicas relevantes:**

- Todas as tabelas usam `bigint generated always as identity` como chave primaria.
- O campo `user_id` em todas as tabelas e do tipo `uuid` e referencia `auth.users(id)` com `on delete cascade`.
- A tabela `profiles` possui constraint `unique` em `user_id`, garantindo um perfil por usuario. Isto permite o uso de `upsert` tanto no frontend (onboarding) quanto no backend.
- As tabelas `workout_logs` e `microcycles` armazenam dados aninhados (series, exercicios) como colunas `jsonb`, evitando tabelas auxiliares excessivas e mantendo compatibilidade com os schemas Pydantic que definem listas de objetos.
- A tabela `check_ins` possui constraint `unique(user_id, check_in_date)`, impedindo mais de um check-in por dia por usuario.
- A tabela `microcycles` possui constraint `check(end_date >= start_date)` para garantir consistencia temporal.
- Todos os campos numericos de check-in possuem `check(campo between 1 and 10)` replicando as validacoes do Pydantic.
- Indices compostos foram criados em `(user_id, data desc)` para otimizar consultas de historico.

**Row Level Security (RLS):**

Todas as quatro tabelas possuem RLS ativado com policies que garantem que cada usuario so pode ler e escrever seus proprios dados. As policies utilizam `auth.uid()` do Supabase para comparacao.

| Tabela | SELECT | INSERT | UPDATE |
|---|---|---|---|
| `profiles` | Sim | Sim | Sim |
| `workout_logs` | Sim | Sim | - |
| `check_ins` | Sim | Sim | - |
| `microcycles` | Sim | Sim | - |

**Trigger:**

A tabela `profiles` possui um trigger `before update` que atualiza automaticamente a coluna `updated_at` para `now()` em cada modificacao.

---

### 2. Configuracao e Ambiente (`backend/config.py` e `backend/.env.example`)

O modulo `config.py` centraliza o carregamento de variaveis de ambiente usando `python-dotenv`. As variaveis sao expostas como constantes tipadas para consumo em todo o backend.

**Variaveis definidas:**

| Variavel | Descricao | Valor Padrao |
|---|---|---|
| `SUPABASE_URL` | URL do projeto Supabase | (obrigatoria) |
| `SUPABASE_SERVICE_KEY` | Service Role Key do Supabase | (obrigatoria) |
| `OLLAMA_BASE_URL` | URL do servico Ollama local | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo LLM a ser utilizado | `llama3` |
| `API_PREFIX` | Prefixo de todas as rotas da API | `/api/v1` |
| `DEBUG` | Ativa modo debug do FastAPI | `false` |

O arquivo `.env.example` serve como template. O desenvolvedor deve copia-lo para `.env` e preencher com credenciais reais. O `.env` ja esta incluido no `.gitignore` do projeto.

---

### 3. Cliente de Banco de Dados (`backend/database.py`)

Factory simples que instancia o cliente `supabase-py` usando a Service Role Key. A funcao `get_supabase_client()` valida que as credenciais estao presentes antes de criar o cliente.

A Service Role Key bypassa as policies de RLS, permitindo que o backend execute operacoes que nao sao possíveis via anon key (por exemplo, leituras cruzadas entre usuarios para analise de tendencias futuras).

---

### 4. DTOs da API (`backend/schemas/api_models.py`)

Os schemas de dominio (`user.py`, `workout_log.py`, etc.) definem a estrutura conceitual das entidades. Os DTOs da API foram criados separadamente para desacoplar o contrato HTTP do modelo de dominio.

**Modelos definidos:**

- `ProfileCreateRequest`: Payload do `POST /profiles`. Reutiliza os enums `FitnessLevel` e `Goal` de `user.py`.
- `ProfileUpdateRequest`: Payload do `PUT /profiles/{user_id}`. Todos os campos sao opcionais para suportar atualizacao parcial.
- `ProfileResponse`: Retorno padrao de todas as operacoes de perfil. Inclui `id`, `created_at` e `updated_at` que nao existem no schema de dominio.

Esta separacao permite que os contratos de API evoluam independentemente dos modelos de dominio. Por exemplo, um campo pode ser exposto na API mas calculado internamente, sem alterar os schemas base.

---

### 5. Endpoints CRUD de Perfil (`backend/routers/profiles.py`)

Router FastAPI com tres endpoints montados sob o prefixo `/api/v1/profiles`:

**GET `/api/v1/profiles/{user_id}`**

- Retorna o perfil completo do praticante.
- Busca na tabela `profiles` filtrando por `user_id`.
- Retorna HTTP 404 se o perfil nao existir.
- Response model: `ProfileResponse`.

**POST `/api/v1/profiles`**

- Cria ou atualiza o perfil do praticante (upsert).
- O `user_id` e recebido via header HTTP `X-User-Id`.
- Realiza upsert com `on_conflict="user_id"`, ou seja, se o perfil ja existir para aquele usuario, os dados sao atualizados.
- Este comportamento e identico ao que o frontend ja faz no onboarding (`supabase.from('profiles').upsert(...)`).
- Retorna HTTP 201 com o perfil criado/atualizado.
- Request body: `ProfileCreateRequest`.
- Response model: `ProfileResponse`.

**PUT `/api/v1/profiles/{user_id}`**

- Atualiza parcialmente o perfil existente.
- Apenas os campos presentes no payload sao modificados (usa `model_dump(exclude_none=True)`).
- Converte enums Pydantic para strings antes de enviar ao Supabase.
- Retorna HTTP 400 se nenhum campo for enviado.
- Retorna HTTP 404 se o perfil nao existir.
- Request body: `ProfileUpdateRequest`.
- Response model: `ProfileResponse`.

---

### 6. Servidor FastAPI (`backend/main.py`)

Ponto de entrada da aplicacao. Configuracoes:

- **CORS**: Permite requisicoes de `http://localhost:3000` e `http://127.0.0.1:3000` (frontend Next.js em dev). Aceita todos os metodos e headers.
- **Routers**: O router de profiles e montado sob `API_PREFIX` (`/api/v1`).
- **Health Check**: Endpoint `GET /health` retorna `{"status": "ok"}` para monitoramento.
- **Documentacao Automatica**: O FastAPI gera automaticamente docs interativos em `/docs` (Swagger UI) e `/redoc`.

**Comando de execucao:**

```bash
uvicorn backend.main:app --reload --port 8000
```

---

### 7. Dependencias (`backend/requirements.txt`)

Atualizado de 1 para 6 dependencias:

| Pacote | Versao Minima | Finalidade |
|---|---|---|
| `pydantic` | 2.0.0 | Validacao de dados e schemas (pre-existente) |
| `fastapi` | 0.115.0 | Framework web assincrono |
| `uvicorn[standard]` | 0.34.0 | Servidor ASGI para rodar o FastAPI |
| `supabase` | 2.0.0 | Cliente Python para o Supabase |
| `python-dotenv` | 1.0.0 | Carregamento de `.env` |
| `httpx` | 0.28.0 | Cliente HTTP assincrono (dependencia do supabase-py e uso futuro com Ollama) |

---

## Compatibilidade com o Frontend Existente

As decisoes de implementacao garantem compatibilidade total com o frontend ja existente:

- A tabela `profiles` usa exatamente os mesmos nomes de coluna que o frontend envia no onboarding (`user_id`, `age`, `weight_kg`, `height_cm`, `fitness_level`, `primary_goal`, `available_equipment`).
- A tabela `workout_logs` usa o mesmo nome referenciado no hook `useWorkoutLog.js`.
- A tabela `check_ins` usa o mesmo nome referenciado no hook `useCheckIn.js`.
- A tabela `microcycles` usa o mesmo nome referenciado no hook `useMicrocycle.js`.
- As colunas de ordenacao (`session_date`, `check_in_date`, `created_at`) correspondem exatamente as queries dos hooks do frontend.

---

## Como Rodar (Dev Mode)

### Requisitos

- Python 3.11+
- Node.js v24+
- Docker Desktop
- Projeto configurado no Supabase Cloud

### Passos

1. Executar o script `backend/db/schema.sql` no SQL Editor do Supabase para criar as tabelas.

2. Copiar o template de ambiente e preencher com credenciais reais:
   ```bash
   cp backend/.env.example backend/.env
   ```

3. Instalar dependencias do backend:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Iniciar o servidor FastAPI:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

5. Subir o servico Ollama (necessario a partir da Fase 3):
   ```bash
   docker compose up -d
   ```

6. Iniciar o frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

O backend estara acessivel em `http://localhost:8000` com documentacao interativa em `http://localhost:8000/docs`.

---

## Fase 2: Motor de Analise de Estado (State Engine)

A Fase 2 implementou o nucleo de inteligencia analitica da aplicacao. O State Engine processa os dados brutos de historico (workout_logs, check_ins, microcycles) e os transforma em indicadores acionaveis de performance e prontidao.

### Arquivos criados na Fase 2

| Arquivo | Descricao |
|---|---|
| `backend/services/state_engine.py` | Modulo principal com todos os algoritmos de calculo |
| `backend/schemas/state_models.py` | DTOs de response tipados para o endpoint de estado |
| `backend/routers/state.py` | Router FastAPI com o endpoint GET /api/v1/state/{user_id} |

### Arquivos modificados na Fase 2

| Arquivo | Alteracao |
|---|---|
| `backend/main.py` | Registrado o state_router sob API_PREFIX |
| `backend/routers/__init__.py` | Exportado state_router |

---

### 8. State Engine (`backend/services/state_engine.py`)

Modulo central da Fase 2. Contem cinco funcoes de busca/calculo e uma funcao orquestradora.

**Funcoes de busca de dados:**

- `_fetch_workout_logs(user_id, since)`: Busca workout_logs do usuario a partir de uma data. Ordena por `session_date desc`.
- `_fetch_check_ins(user_id, since)`: Busca check-ins a partir de uma data. Ordena por `check_in_date desc`.
- `_fetch_latest_microcycle(user_id)`: Busca o microciclo mais recente (por `created_at desc`, limit 1).

**1. compute_volume_metrics(logs)**

Calcula metricas de volume e intensidade a partir de uma lista de workout_logs.

O campo `sets` dos logs e armazenado como JSONB no banco e pode chegar como lista de dicts ou como string JSON. O modulo trata ambos os casos.

Metricas calculadas:
- `total_sets`: contagem de todas as series no periodo.
- `total_tonnage`: somatorio de (reps x weight_kg) de cada serie.
- `avg_rpe`: media ponderada de RPE de todas as series que possuem RPE registrado.
- `sessions_count`: numero de sessoes no periodo.
- `avg_duration_minutes`: duracao media das sessoes em minutos.
- `volume_per_exercise`: dict indexado pelo nome do exercicio, contendo sets, tonelagem e RPE medio de cada um.

Esta funcao e chamada duas vezes pelo orquestrador: uma com os logs dos ultimos 7 dias (volume semanal) e outra com os dos ultimos 30 dias (volume mensal). Isso permite ao modulo de IA (Fase 3) comparar a carga recente com a carga historica.

**2. compute_fatigue_index(check_ins)**

Calcula a fadiga acumulada comparando os check-ins recentes (7 dias) com o baseline (30 dias).

Para cada um dos 5 campos do check-in (sleep_quality, energy_level, muscle_soreness, stress_level, fatigue_level):
- Calcula a media dos ultimos 7 dias (`recent_avg`).
- Calcula a media dos ultimos 30 dias (`baseline_avg`).
- Calcula o delta (`recent_avg - baseline_avg`).

Interpracao dos deltas:
- `fatigue_level`, `muscle_soreness`, `stress_level`: delta positivo indica piora.
- `sleep_quality`, `energy_level`: delta negativo indica piora.

Alem disso, calcula um `readiness_score` consolidado (0-100) usando a formula:

```
readiness = ((avg_positivos / 10) * 50) + (((10 - avg_negativos) / 10) * 50)
```

Onde positivos = [sleep_quality, energy_level] e negativos = [muscle_soreness, stress_level, fatigue_level]. Um score acima de 65 indica boa prontidao; abaixo de 40 sugere necessidade de deload.

**3. compute_adherence(logs, microcycle)**

Calcula o indice de adesao comparando sessoes prescritas vs realizadas.

- Conta o numero de workouts no campo `workouts` (JSONB) do microciclo mais recente.
- Filtra os workout_logs que caem dentro do intervalo [start_date, end_date] do microciclo.
- Calcula `adherence_rate = completed / prescribed`.

Retorna None se nao houver microciclo para comparar. Isto e importante para usuarios novos que ainda nao tem historico de prescricao.

**4. compute_tolerated_volume(logs)**

Detecta o ponto de queda de performance por exercicio.

Agrupamento: todas as series de todos os logs sao agrupadas por `exercise_name`.

Deteccao de tendencia: para cada exercicio, divide os dados em primeira e segunda metade cronologica.
- Se o RPE medio da segunda metade for > 0.5 pontos acima da primeira: `degrading` (volume excedeu recuperacao).
- Se o RPE medio da segunda metade for > 0.5 pontos abaixo da primeira: `improving`.
- Adicional: se a carga media da segunda metade caiu > 5% em relacao a primeira, marca como `degrading` (exceto se ja estava melhorando).

Retorna um dict indexado pelo nome do exercicio com `total_sets_in_period`, `avg_rpe`, `avg_weight_kg` e `trend`.

**5. build_practitioner_state(user_id)** — Funcao orquestradora

Funcao principal chamada pelo endpoint. Executa a sequencia:
1. Busca todos os workout_logs dos ultimos 30 dias.
2. Filtra os dos ultimos 7 dias a partir do resultado.
3. Busca todos os check_ins dos ultimos 30 dias.
4. Busca o microciclo mais recente.
5. Chama as 4 funcoes de calculo.
6. Retorna o report consolidado.

Constantes configuradas:
- `RECENT_WINDOW_DAYS = 7`
- `BASELINE_WINDOW_DAYS = 30`

---

### 9. Response Models do State Engine (`backend/schemas/state_models.py`)

Modelos Pydantic que tipam a resposta do endpoint de estado. Garantem validacao automatica e documentacao no Swagger.

| Modelo | Descricao |
|---|---|
| `PeriodInfo` | Janelas temporais usadas nos calculos (7d, 30d) |
| `ExerciseVolume` | Volume de um exercicio individual (sets, tonelagem, RPE) |
| `VolumeMetrics` | Consolidado de volume: total_sets, tonelagem, RPE medio, sessoes, duracao, breakdown por exercicio |
| `FatigueAnalysis` | Analise de fadiga: medias recente e baseline, deltas, readiness_score |
| `AdherenceMetrics` | Adesao: sessoes prescritas vs realizadas, taxa |
| `ExerciseTolerance` | Tolerancia por exercicio: sets no periodo, RPE, carga media, tendencia |
| `PractitionerStateResponse` | Response principal que agrupa todos os modelos acima |

---

### 10. Endpoint de Estado (`backend/routers/state.py`)

Router FastAPI com um unico endpoint:

**GET `/api/v1/state/{user_id}`**

- Chama `build_practitioner_state(user_id)` do State Engine.
- Valida o retorno contra `PractitionerStateResponse`.
- Retorna HTTP 500 com detalhes se qualquer calculo falhar.
- Response model: `PractitionerStateResponse`.

Exemplo de response (estrutura):

```json
{
  "user_id": "uuid-do-usuario",
  "generated_at": "2026-04-20",
  "period": {
    "recent_window_days": 7,
    "baseline_window_days": 30
  },
  "weekly_volume": {
    "total_sets": 45,
    "total_tonnage": 12500.0,
    "avg_rpe": 7.2,
    "sessions_count": 4,
    "avg_duration_minutes": 62.5,
    "volume_per_exercise": {
      "Supino Reto": {"sets": 12, "tonnage": 4800.0, "avg_rpe": 7.5},
      "Agachamento": {"sets": 10, "tonnage": 5200.0, "avg_rpe": 8.0}
    }
  },
  "monthly_volume": { ... },
  "fatigue_analysis": {
    "recent_avg": {"sleep_quality": 6.5, "fatigue_level": 7.2, ...},
    "baseline_avg": {"sleep_quality": 7.1, "fatigue_level": 5.8, ...},
    "delta": {"sleep_quality": -0.6, "fatigue_level": 1.4, ...},
    "readiness_score": 42.5,
    "data_points_recent": 5,
    "data_points_baseline": 22
  },
  "adherence": {
    "prescribed_sessions": 5,
    "completed_sessions": 4,
    "adherence_rate": 0.80
  },
  "tolerated_volume": {
    "Supino Reto": {"total_sets_in_period": 48, "avg_rpe": 7.8, "avg_weight_kg": 80.0, "trend": "stable"},
    "Agachamento": {"total_sets_in_period": 40, "avg_rpe": 8.5, "avg_weight_kg": 100.0, "trend": "degrading"}
  }
}
```

---

## Fase 3: Orquestracao de IA e Geracao Adaptativa

A Fase 3 implementou a integracao completa com o servico Ollama para geracao automatica de microciclos de treino. O modulo recebe o perfil do praticante e seu estado consolidado (calculado pelo State Engine da Fase 2) e os transforma em uma prescricao de treino personalizada via LLM.

### Arquivos criados na Fase 3

| Arquivo | Descricao |
|---|---|
| `backend/services/llm_service.py` | Cliente Ollama, gerador de prompt, parser JSON, validador e persistencia |
| `backend/schemas/microcycle_models.py` | DTOs de request/response para o endpoint de geracao |
| `backend/routers/microcycle.py` | Router com endpoints de geracao e health check |
| `backend/tests/test_parser.py` | Teste do parser de JSON do LLM |

### Arquivos modificados na Fase 3

| Arquivo | Alteracao |
|---|---|
| `backend/main.py` | Registrado o microcycle_router sob API_PREFIX |
| `backend/routers/__init__.py` | Exportado microcycle_router |

---

### 11. Servico LLM (`backend/services/llm_service.py`)

Modulo central da Fase 3. Organizado em 5 componentes com responsabilidades bem definidas.

**11.1. OllamaClient**

Classe que encapsula a comunicacao HTTP com a API REST do Ollama. Usa `httpx.AsyncClient` para requisicoes assincronas e non-blocking.

Configuracoes:
- `base_url`: endereco do Ollama (default: `http://localhost:11434` via config.py)
- `model`: modelo LLM a ser usado (default: `llama3` via config.py)
- `timeout`: timeout de resposta (default: 120 segundos)
- `temperature`: 0.7 (balanco entre criatividade e previsibilidade)

Metodo `generate(prompt, system)`: envia requisicao ao endpoint `/api/generate` com `stream=false` para receber a resposta completa de uma vez.

Tratamento de erros mapeado para excecoes semanticas:
- `httpx.ConnectError` -> `ConnectionError` (Ollama nao esta rodando)
- `httpx.TimeoutException` -> `TimeoutError` (modelo muito grande ou lento)
- `httpx.HTTPStatusError` -> `RuntimeError` (erro HTTP do Ollama)

Metodo `check_health()`: GET simples na URL base para verificar se o servico esta acessivel.

**11.2. Gerador de Prompt**

Dois componentes:

`SYSTEM_PROMPT` (constante): instrucoes fixas para o LLM. Define:
- O papel do modelo (personal trainer especialista em periodizacao).
- 7 regras obrigatorias (formato JSON, adaptacao ao nivel, fadiga, deload, equipamentos, justificativa).
- A estrutura JSON exata esperada na resposta, replicando o schema de `microcycle.py`.

`build_user_prompt(profile, state)`: constroi o prompt contextualizado comcados reais do praticante. Organizado em secoes:
- PERFIL DO PRATICANTE: dados demograficos e preferencias do onboarding.
- ESTADO ATUAL: metricas de volume dos ultimos 7 dias.
- ANALISE DE FADIGA: readiness_score e deltas.
- ADESAO: prescrito vs realizado.
- TENDENCIAS POR EXERCICIO: trend detection do tolerated volume.

**11.3. Parser de Resposta**

`extract_json_from_response(raw)`: extrai JSON valido da resposta do LLM. Trata tres cenarios:
1. Resposta e JSON puro.
2. JSON envolto em blocos de markdown (````json ... ````).
3. JSON misturado com texto explicativo antes/depois (busca pelo primeiro `{` e ultimo `}`).

**11.4. Validador Estrutural**

`validate_microcycle_structure(data)`: valida e normaliza o dict extraido. Garante que:
- O campo `workouts` existe e e uma lista nao-vazia.
- Cada sessao possui `session_name`, `day_of_week` (1-7) e `exercises` nao-vazio.
- Cada exercicio possui todos os 5 campos obrigatorios com tipos corretos.
- `target_rpe` esta no range 1-10.
- `max_rpe_cap` esta no range 1-10.
- Aplica defaults razoaveis para campos ausentes (ex: `rest_seconds=90`, `target_reps="8-12"`).

**11.5. Orquestrador de Geracao**

`generate_microcycle(user_id, profile, state)`: funcao principal. Fluxo:
1. Instancia `OllamaClient`.
2. Constroi o prompt via `build_user_prompt`.
3. Envia ao Ollama.
4. Parseia e valida a resposta.
5. Calcula as datas do microciclo (proxima segunda a domingo).
6. Retorna o dict pronto para persistencia.

Implementa retry com `LLM_MAX_RETRIES=2`: se a resposta nao for parseavel (JSON malformado, campos ausentes), tenta novamente automaticamente.

**11.6. Persistencia**

`persist_microcycle(microcycle)`: insere o microciclo na tabela `microcycles` do Supabase. O campo `workouts` e serializado como JSON string antes da insercao. Retorna o registro inserido com `id` e `created_at` gerados pelo banco.

---

### 12. Response Models da Geracao (`backend/schemas/microcycle_models.py`)

Modelos Pydantic para o endpoint de geracao:

| Modelo | Descricao |
|---|---|
| `GenerateMicrocycleRequest` | Payload do POST. Contem apenas `user_id` (perfil e estado sao buscados internamente) |
| `ExercisePrescriptionResponse` | Exercicio prescrito (nome, sets, reps, RPE, descanso) |
| `WorkoutSessionResponse` | Sessao de treino com lista de exercicios |
| `MicrocycleResponse` | Microciclo completo com campos do banco (id, created_at) |
| `GenerationStatusResponse` | Envelope de resposta com status, microciclo e mensagem |

---

### 13. Endpoints de Microciclo (`backend/routers/microcycle.py`)

Router com dois endpoints montados sob `/api/v1/microcycle`:

**POST `/api/v1/microcycle/generate`**

Endpoint principal de geracao. Orquestra todo o fluxo:
1. Busca o perfil do praticante (retorna 404 se nao existir).
2. Calcula o estado via State Engine.
3. Gera o microciclo via LLM.
4. Persiste no banco.
5. Retorna o microciclo com status "success".

Codigos HTTP de erro mapeados:
- `404`: perfil nao encontrado (onboarding incompleto).
- `502`: LLM retornou resposta invalida apos todos os retries.
- `503`: Ollama nao esta acessivel (Docker parado).
- `504`: timeout na resposta do Ollama.
- `500`: erro interno no calculo de estado ou na persistencia.

Request body:
```json
{
  "user_id": "uuid-do-usuario"
}
```

Response (status 201):
```json
{
  "status": "success",
  "microcycle": {
    "id": 1,
    "user_id": "uuid",
    "start_date": "2026-04-27",
    "end_date": "2026-05-03",
    "workouts": [
      {
        "session_name": "Treino A - Peito e Triceps",
        "day_of_week": 1,
        "exercises": [
          {
            "exercise_name": "Supino Reto",
            "target_sets": 4,
            "target_reps": "8-12",
            "target_rpe": 7,
            "rest_seconds": 90
          }
        ]
      }
    ],
    "ai_justification": "Justificativa detalhada...",
    "max_weekly_sets_per_muscle": 16,
    "max_rpe_cap": 8,
    "created_at": "2026-04-20T23:22:00Z"
  },
  "message": "Microciclo gerado com 4 sessoes para o periodo 2026-04-27 a 2026-05-03."
}
```

**GET `/api/v1/microcycle/health`**

Verifica se o servico Ollama esta acessivel e retorna o modelo configurado. Util para debug e monitoramento.

---

## Fase 4: Validacao de Seguranca e Finalizacao da API

A Fase 4 completou a aplicacao com a camada de seguranca pos-IA e todos os endpoints CRUD restantes. O Safety Validator garante que nenhum microciclo gerado pela IA exceda os limites fisiologicos seguros, enquanto os endpoints de sessao permitem que o frontend registre e consulte dados de treino e prontidao.

### Arquivos criados na Fase 4

| Arquivo | Descricao |
|---|---|
| `backend/services/safety_validator.py` | Validador de seguranca com limites dinamicos, deload e ajuste de RPE |
| `backend/schemas/session_models.py` | DTOs de request/response para workout logs, check-ins e historico |
| `backend/routers/sessions.py` | Router com 6 endpoints: CRUD de sessoes, check-ins e evolucao de carga |

### Arquivos modificados na Fase 4

| Arquivo | Alteracao |
|---|---|
| `backend/routers/microcycle.py` | Integrado safety_validator entre a geracao LLM e a persistencia (step 3.5) |
| `backend/main.py` | Registrado sessions_router |
| `backend/routers/__init__.py` | Exportado sessions_router |

---

### 14. Validador de Seguranca (`backend/services/safety_validator.py`)

Camada de protecao que atua DEPOIS da geracao pela IA e ANTES da persistencia. Garante que, independente do que o LLM sugira, o microciclo respeita limites fisiologicos seguros.

**14.1. Limites de Volume por Nivel**

Caps de series semanais por grupo muscular, baseados em diretrizes de periodizacao:

| Nivel | Max Sets/Semana/Musculo |
|---|---|
| Beginner | 12 |
| Intermediate | 18 |
| Advanced | 25 |

**14.2. Logica de Deload Automatico**

Tres faixas de prontidao baseadas no `readiness_score` do State Engine:

| Readiness Score | Acao | Volume | RPE Max |
|---|---|---|---|
| < 40 | DELOAD FORCADO | 50% do normal | 6 |
| 40-55 | VOLUME REDUZIDO | 70% do normal | 8 |
| > 55 | NORMAL | 100% | 10 |

Quando deload e forcado, o descanso entre series tambem e aumentado para minimo 120s.

**14.3. Ajuste Dinamico de RPE**

O RPE cap e reduzido em 1 ponto por cada flag ativo:
- Qualidade do sono <= 4 (media dos ultimos 7 dias)
- Estresse >= 7 (media dos ultimos 7 dias)

O RPE nunca fica abaixo de 5, independente do numero de flags.

**14.4. Enforcement de Caps**

`enforce_safety_caps(microcycle, caps)` aplica os limites calculados ao microciclo:
1. Clamp de RPE de cada exercicio para respeitar o `max_rpe_cap`.
2. Reducao proporcional de sets se o volume total de um exercicio exceder o cap (minimo 2 sets).
3. Aumento de descanso para minimo 120s em semanas de deload.
4. Atualizacao dos metadados `max_weekly_sets_per_muscle` e `max_rpe_cap` do microciclo.
5. Anexacao de um bloco `[VALIDACAO DE SEGURANCA]` na `ai_justification` com todas as regras ativadas e ajustes aplicados (audit trail).

**14.5. Funcao de Orquestracao**

`validate_and_enforce(microcycle, fitness_level, fatigue_analysis)`: funcao chamada pelo router. Extrai `readiness_score`, `sleep_quality` e `stress_level` da analise de fadiga, calcula os caps dinamicos e aplica-os.

---

### 15. DTOs de Sessao (`backend/schemas/session_models.py`)

Modelos Pydantic que tipam os endpoints de sessao e historico:

| Modelo | Descricao |
|---|---|
| `SetLogRequest` | Uma serie executada (exercicio, reps, carga, RPE) |
| `WorkoutLogCreateRequest` | Payload completo de sessao (user_id, data, nome, duracao, series, notas) |
| `SetLogResponse` / `WorkoutLogResponse` | Retorno da API com campos do banco (id, created_at) |
| `CheckInCreateRequest` | Payload de check-in diario (5 metricas: sono, energia, dor, estresse, fadiga) |
| `CheckInResponse` | Retorno do check-in com campos do banco |
| `ExerciseProgressEntry` | Ponto de dados de evolucao (data, sets, reps, carga max, RPE medio) |
| `ExerciseProgressResponse` | Historico agrupado por exercicio |
| `WorkoutHistoryResponse` | Resumo completo com lista de sessoes e range de datas |

---

### 16. Endpoints de Sessao (`backend/routers/sessions.py`)

Router com 6 endpoints montados sob `/api/v1/sessions`:

**POST `/api/v1/sessions/workout-log`**

- Registra uma sessao de treino executada.
- O campo `sets` e serializado como JSON string para armazenamento JSONB.
- Retorna HTTP 201 com o registro inserido.
- Request body: `WorkoutLogCreateRequest`.
- Response: `WorkoutLogResponse`.

**GET `/api/v1/sessions/workout-log/{log_id}`**

- Busca um registro de sessao por ID.
- Retorna HTTP 404 se nao encontrado.
- Response: `WorkoutLogResponse`.

**GET `/api/v1/sessions/history/{user_id}`**

- Retorna o historico de sessoes do praticante.
- Parametros de query: `days` (default 30), `limit` (default 50).
- Inclui `date_range` com a primeira e ultima data do periodo.
- Response: `WorkoutHistoryResponse`.

**GET `/api/v1/sessions/progress/{user_id}`**

- Retorna a evolucao de carga por exercicio.
- Agrupa dados por sessao e exercicio, calculando sets, reps, carga maxima e RPE medio.
- Parametros de query: `exercise` (filtro opcional), `days` (default 90).
- Response: `list[ExerciseProgressResponse]`.

**POST `/api/v1/sessions/check-in`**

- Registra um check-in diario de prontidao.
- Realiza upsert com `on_conflict="user_id,check_in_date"` — se ja existir check-in para aquele dia, atualiza.
- Retorna HTTP 201 com o registro inserido/atualizado.
- Request body: `CheckInCreateRequest`.
- Response: `CheckInResponse`.

**GET `/api/v1/sessions/check-ins/{user_id}`**

- Retorna os check-ins do praticante ordenados por data decrescente.
- Parametros de query: `days` (default 30), `limit` (default 30).
- Response: `list[CheckInResponse]`.

---

### 17. Integracao do Safety Validator no Pipeline de Geracao

O fluxo do endpoint `POST /api/v1/microcycle/generate` foi atualizado para incluir o passo 3.5:

```
1. Buscar perfil      (profiles table)
2. Calcular estado    (State Engine)
3. Gerar via LLM      (Ollama)
3.5. Validar seguranca (Safety Validator)  <-- NOVO
4. Persistir           (microcycles table)
5. Retornar            (API response)
```

O validador recebe o `fitness_level` do perfil e o `fatigue_analysis` do estado para calcular caps dinamicos. Os ajustes sao aplicados ANTES da persistencia, garantindo que nunca um microciclo inseguro seja salvo no banco.

---

## API Completa (Todos os Endpoints)

| Metodo | Rota | Descricao | Fase |
|---|---|---|---|
| GET | `/health` | Health check do servidor | 1 |
| GET | `/api/v1/profiles/{user_id}` | Buscar perfil | 1 |
| POST | `/api/v1/profiles` | Criar/atualizar perfil (upsert) | 1 |
| PUT | `/api/v1/profiles/{user_id}` | Atualizar perfil parcialmente | 1 |
| GET | `/api/v1/state/{user_id}` | Estado consolidado do praticante | 2 |
| POST | `/api/v1/microcycle/generate` | Gerar microciclo via IA | 3+4 |
| GET | `/api/v1/microcycle/health` | Health check do Ollama | 3 |
| POST | `/api/v1/sessions/workout-log` | Registrar sessao de treino | 4 |
| GET | `/api/v1/sessions/workout-log/{id}` | Buscar log por ID | 4 |
| GET | `/api/v1/sessions/history/{user_id}` | Historico de sessoes | 4 |
| GET | `/api/v1/sessions/progress/{user_id}` | Evolucao de carga por exercicio | 4 |
| POST | `/api/v1/sessions/check-in` | Registrar check-in diario | 4 |
| GET | `/api/v1/sessions/check-ins/{user_id}` | Historico de check-ins | 4 |

---

## Conclusao

Todas as 4 fases do DEV 2 estao implementadas. O backend da aplicacao Adaptive Training AI agora possui:

- Persistencia completa com PostgreSQL (Supabase) com RLS e constraints.
- Motor de estado que calcula metricas de volume, fadiga, adesao e tolerancia.
- Gerador de microciclos integrado com LLM (Ollama) com retry e parsing robusto.
- Validador de seguranca pos-IA com deload automatico e ajuste dinamico de RPE.
- CRUD completo para todas as entidades: perfis, sessoes de treino, check-ins e historico.
- 13 endpoints REST documentados automaticamente via Swagger UI em `/docs`.
