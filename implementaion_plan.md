# Plano de Implementação: Micro SAAS - Prescrição Adaptativa (Versão Supabase Cloud)

Este documento detalha o planejamento para a frente de **Infraestrutura, Frontend e Integração**, agora utilizando o Supabase Cloud como núcleo de dados e autenticação.

---

## 1. Infraestrutura Híbrida
A arquitetura combina serviços gerenciados (Cloud) com processamento local de IA.

### Cloud (Supabase):
* [cite_start]**PostgreSQL**: Persistência de perfis, sessões de treino e logs de execução.

* **Supabase Auth**: Gerenciamento de usuários e proteção de rotas.
* **Storage**: Armazenamento de arquivos ou documentos de referência, se necessário.

### Local (Docker):
* [cite_start]**Ollama**: Execução dos modelos de linguagem (ex: Llama 3 ou Mistral) para o motor de adaptação e gerador de justificativas.

---

## 2. Contratos de Dados (Schemas Pydantic)
Os modelos validam os dados antes da persistência no Supabase e na comunicação com os serviços de IA.

* [cite_start]**UserSchema**: Dados de onboarding alinhados ao "Perfil Base"[cite: 171, 172].
* [cite_start]**WorkoutLogSchema**: Registros de execução para o "Modelo Dinâmico do Praticante"[cite: 5, 153].
* [cite_start]**CheckInSchema**: Dados de prontidão, fadiga e recuperação semanal[cite: 10, 156].
* [cite_start]**MicrocycleSchema**: Estrutura do treino adaptado com metadados de segurança[cite: 174, 180].

---

## 3. Desenvolvimento Frontend (Next.js + Supabase SDK)
[cite_start]O frontend será o ponto de entrada para todas as interações do praticante[cite: 185, 186].

### Fluxos Principais:
1. [cite_start]**Onboarding & Auth**: Registro via Supabase Auth e preenchimento da anamnese inicial (objetivo, nível, equipamentos)[cite: 172, 191].
2. [cite_start]**Dashboard de Performance**: Visualização de tendências de carga e métricas calculadas (volume semanal, RPE médio)[cite: 119, 122, 169].
3. [cite_start]**Registro de Sessão**: Interface para input em tempo real de cargas e repetições[cite: 161, 191].
4. [cite_start]**Visualização do Microciclo**: Exibição do treino com justificativas geradas pela IA[cite: 40, 127].

---

## 4. Integração e Segurança
[cite_start]A integração deve garantir que as restrições de segurança [cite: 64, 180] sejam aplicadas antes da exibição final ao usuário.

* **Orquestração**: O frontend consome dados do Supabase e solicita a geração de novos planos ao serviço de IA (Ollama).
* [cite_start]**Camada de Segurança**: Implementação de lógica que valide os limites de volume e intensidade antes de persistir o novo microciclo no banco[cite: 32, 180].
* **Documentação**: Guia de configuração das chaves de API do Supabase e instruções para o ambiente Docker local.

---
**Base de Referência:**
* [cite_start]TCC: *Arquitetura de IA para Prescrição Adaptativa* [cite: 1]
* [cite_start]Arquitetura C4 (Níveis 1, 2 e 3) [cite: 105, 193, 235]