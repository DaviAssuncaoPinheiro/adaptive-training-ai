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

## Arquitetura Atual (Apos Fase 1)

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

  schemas/
    __init__.py                # (pre-existente)
    user.py                    # (pre-existente)
    workout_log.py             # (pre-existente)
    check_in.py                # (pre-existente)
    microcycle.py              # (pre-existente)
    api_models.py              # DTOs de request/response da API

  services/
    __init__.py                # Preparado para Fases 2 e 3
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

## Proximos Passos (Fases 2, 3 e 4)

- **Fase 2 (Motor de Estado)**: Implementar algoritmos de calculo de volume acumulado, fadiga, adesao e volume tolerado em `backend/services/state_engine.py`. Expor via endpoint `GET /api/v1/state/{user_id}`.
- **Fase 3 (Geracao de Microciclo)**: Integrar com Ollama para geracao de treinos adaptativos em `backend/services/llm_service.py`. Expor via endpoint `POST /api/v1/generate-microcycle`.
- **Fase 4 (Seguranca)**: Implementar validadores de Safety Caps, logica de deload automatico e endpoints de sessao e historico.
