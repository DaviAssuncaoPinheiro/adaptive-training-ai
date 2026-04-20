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
Certifique-se de que o arquivo `.env` na raiz do projeto contém as chaves do seu projeto Supabase:
```env
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua-chave-anon-key
```

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