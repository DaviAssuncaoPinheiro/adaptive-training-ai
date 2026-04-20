# Adaptive Training AI — Documentação Técnica

Este documento serve como guia técnico para desenvolvedores sobre o estado atual da aplicação **Adaptive Training AI**, um Micro SAAS para prescrição adaptativa de treinos utilizando Inteligência Artificial híbrida.

---

## 🚀 Arquitetura Geral

A aplicação utiliza uma arquitetura **Híbrida**, separando persistência global e autenticação em nuvem do processamento pesado de IA local.

1.  **Cloud (Supabase)**: Gerencia Autenticação (Auth) e Banco de Dados (PostgreSQL).
2.  **Local (Docker/Ollama)**: Executa modelos de linguagem (LLMs) localmente para geração de treinos, garantindo privacidade e custo zero de inferência.
3.  **Frontend (Next.js 15)**: Interface do usuário SPA com App Router, integrando ambos os mundos.

---

## 🛠 Tech Stack

-   **Frontend**: Node.js, Next.js 15 (App Router), React 19.
-   **Estilização**: Vanilla CSS (CSS Modules) com Design System focado em Dark Mode/Glassmorphism.
-   **Backend (Contratos)**: Python 3.13, Pydantic v2 (para validação rigorosa de dados).
-   **Banco/Auth**: Supabase Cloud (PostgreSQL).
-   **Infra de IA**: Docker + Ollama (Llama 3 / Mistral).
-   **Visualização**: Recharts (Gráficos de performance).

---

## 📂 Estrutura do Projeto

### 1. Contratos de Dados (`/backend/schemas/`)
Modularizado para garantir que o Frontend e o Motor de IA falem a mesma língua:
-   `user.py`: Perfil demográfico e objetivos.
-   `workout_log.py`: Registros de execução de exercícios (séries, reps, carga, RPE).
-   `check_in.py`: Métricas diárias de prontidão (sono, dor, fadiga).
-   `microcycle.py`: Estrutura da semana de treino prescrita + Justificativa da IA + *Safety Caps*.

### 2. Frontend (`/frontend/`)
Organizado seguindo as melhores práticas de escalabilidade:
-   `src/app/`: Roteamento e layouts. Subdividido em grupos `(auth)` para login/registro e `(authenticated)` para áreas logadas.
-   `src/components/`: Componentes de UI reutilizáveis (UI Pura) separados da lógica.
-   `src/hooks/`: Toda a lógica de comunicação com Supabase (useAuth, useWorkoutLog, etc).
-   `src/context/`: `AuthProvider` para gerenciamento global de sessão.
-   `src/lib/`: Configurações de cliente Supabase (Browser/Server) e utilitários.

### 3. Infraestrutura (`/docker-compose.yml`)
Configuração pronta para subir o serviço **Ollama**.
-   **Imagem**: `ollama/ollama:0.1.25`
-   **Porta**: `11434`
-   **Volumes**: Persistência de modelos em `ollama_data`.

---

## 🔐 Segurança e Proteção de Rotas

Implementamos um **Next.js Middleware** (`middleware.js`) que intercepta todas as rotas:
-   Usuários não autenticados são forçados para `/login`.
-   Usuários autenticados não podem acessar `/login` ou `/register` (redirect automático para `/dashboard`).
-   O gerenciamento de sessão é feito via cookies seguros sincronizados com o Supabase Auth.

---

## ✨ Funcionalidades Implementadas

1.  **Auth Flow**: Registro e Login completos com Supabase.
2.  **Onboarding Wizard**: Formulário multi-step para anamnese inicial.
3.  **Dashboard**: Gráficos de evolução de volume e tendência de RPE (Percepção de Esforço).
4.  **Session Logger**: Registro dinâmico de treinos (permite adicionar/remover séries em tempo real).
5.  **Microcycle View**: Visualização do plano semanal com badges de segurança e justificativa do motor de IA.

---

## 🏃 Como Rodar (Dev Mode)

### Requisitos
-   Node.js v24+
-   Docker Desktop
-   Projeto no Supabase Cloud

### Passos
1.  **Vincular Env**: Tenha um `.env` na raiz e execute o sync para o frontend.
2.  **Subir IA**: `docker compose up -d` na raiz.
3.  **Rodar Front**: 
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

---

## 📌 Próximos Passos (Fase 4)
-   Implementar a **Orquestração**: Conectar o frontend ao Ollama via API local.
-   **Camada de Segurança**: Lógica de verificação dos *Safety Caps* antes da escrita no Banco.
-   **Documentação da API**: Especificar os endpoints do controlador de IA.
