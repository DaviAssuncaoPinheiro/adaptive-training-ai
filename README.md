# Adaptive Training AI ⚡

Este projeto é uma plataforma de prescrição adaptativa de treinos que combina **Next.js**, **Supabase** e **IA Local (Ollama)**.

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado em sua máquina:
- **Node.js** (v24.0.0 ou superior)
- **Docker Desktop** (para rodar a IA local)
- uma conta no **Supabase Cloud**

---

## 🛠️ Inicialização do Projeto

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

### 1. Variáveis de Ambiente

**Frontend (`frontend/.env.local`)**
```env
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua-chave-anon-key
# Onde o BFF (Next API route) chama o FastAPI server-side:
FASTAPI_URL=http://localhost:8000
```

**Backend (`backend/.env`)**
```env
NCBI_ENTREZ_EMAIL=voce@exemplo.com
OLLAMA_HOST=http://localhost:11434
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-chave-anon-key
# Encontre em: Supabase Dashboard → Project Settings → API → JWT Settings → JWT Secret
SUPABASE_JWT_SECRET=seu-jwt-secret
```

### 1.1 Migrações SQL

As migrations vivem em `supabase/migrations/` (formato Supabase CLI):

| Arquivo | O que cria |
| --- | --- |
| `20240421000001_create_tables.sql` | Tabelas `profiles`, `check_ins`, `workout_logs`, `microcycles` |
| `20240421000002_rls_policies.sql`  | Políticas RLS owner-scoped para as 4 tabelas |
| `20260426000001_add_microcycle_jobs.sql` | Tabela `microcycle_jobs` (geração assíncrona) + RLS |

**Aplique cada uma em ordem** no Supabase Dashboard → SQL Editor (ou via
`supabase db push` se você tiver a CLI configurada).


### 2. Infraestrutura de IA (Ollama)
Para iniciar o motor de IA local, execute no terminal da raiz:
```bash
docker compose up -d
```
*Isso vai baixar e rodar o container do Ollama na porta 11434.*

### 3. Frontend (Next.js)
Navegue até a pasta frontend e instale as dependências:
```bash
cd frontend
npm install
npm run dev
```
Acesse [http://localhost:3000](http://localhost:3000) no seu navegador.

### 4. Backend API (FastAPI)
From the `backend/` directory:
```bash
python -m venv .venv
. .venv/Scripts/activate     # Windows bash — use .venv/bin/activate on Unix
pip install -r requirements.txt
uvicorn api_server:app --reload --port 8000
```

Before the first request, pull the required Ollama models (once):
```bash
docker exec -it ollama_service ollama pull llama3.1
docker exec -it ollama_service ollama pull nomic-embed-text
```

> **Sem ingestão manual.** A justificativa do microciclo é gerada por um agente
> com `PubmedTools`, que busca abstracts no PubMed em tempo real a cada
> geração. Não precisa popular base nenhuma — basta `NCBI_ENTREZ_EMAIL` setado
> em `backend/.env`.
>
> Se quiser **cachear artigos full-text localmente** pra acelerar (opcional),
> ainda dá pra rodar:
> ```bash
> python -m rag.pubmed_ingestor --query "resistance training hypertrophy" --max 25
> ```

---

## 📦 Dependências Principais

### Frontend (`/frontend`)
- **Next.js / React**: Framework principal.
- **@supabase/supabase-js**: Cliente para comunicação com o banco/auth.
- **recharts**: Biblioteca de gráficos para o Dashboard.

### Backend/Schemas (`/backend`)
- **pydantic**: Utilizado para definir os contratos de dados que a IA e o Frontend consomem.

---

## 🏗️ Estrutura de Pastas
- `/frontend`: Aplicação Next.js (App Router).
- `/backend/schemas`: Contratos de dados em Python/Pydantic.
- `docker-compose.yml`: Configuração da infraestrutura local.

Para detalhes técnicos sobre o funcionamento da aplicação, consulte o arquivo [DOCUMENTATION.md](./DOCUMENTATION.md).