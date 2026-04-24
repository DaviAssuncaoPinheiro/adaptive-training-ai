# Plano de Implementacao: DEV 2 - Logica de Treino e Geracao de Microciclo

Este documento descreve as etapas tecnicas para a implementacao do motor de inteligencia e persistencia de dados do Adaptive Training AI. O objetivo e consolidar o estado do praticante, gerir o historico de treinamento e automatizar a geracao de microciclos atraves de modelos de linguagem locais.

---

## Fase 1: Infraestrutura de Dados e Gestao de Perfil
Nesta fase, sera estabelecida a base de persistencia no Supabase e a interface de comunicacao inicial para dados demograficos.

1. Persistencia no PostgreSQL (Supabase):
   - Implementacao da tabela 'profiles' utilizando como base o schema 'user.py'. Campos obrigatorios: user_id (UUID), idade, peso, altura, nivel_fitness, objetivo e equipamentos.
   - Implementacao da tabela 'workout_sessions' para registros historicos (workout_log.py).
   - Implementacao da tabela 'check_ins' para metricas diarias de prontidao (check_in.py).
   - Implementacao da tabela 'microcycles' para armazenamento dos planos gerados.
   - Configuracao de integracao com Supabase Auth para garantir que 'user_id' seja vinculado automaticamente a sessao do usuario.

2. Servicos de CRUD de Perfil (Backend):
   - Configuracao do boilerplate FastAPI no diretorio 'backend'.
   - Criacao de endpoints para criacao, leitura e atualizacao do perfil do usuario.
   - Validacao estrita de tipos utilizando os schemas Pydantic ja definidos.

---

## Fase 2: Motor de Analise de Estado (State Engine)
Desenvolvimento da logica matematica para transformar registros brutos em indicadores de performance.

1. Processamento de Volume e Intensidade:
   - Desenvolvimento de algoritmos para calculo de volume total por agrupamento muscular.
   - Implementacao de calculo de tonelagem e intensidade relativa (RPE medio) por sessao.

2. Analise de Tendencias e Prontidao:
   - Script para calculo de Fadiga Acumulada: Comparativo entre as metricas de 'check_in' dos ultimos 7 dias em relacao a media de 30 dias.
   - Calculo de Indice de Adesao: Razao entre exercicios prescritos no microciclo vs. exercicios efetivamente logados.
   - Definicao do Volume Tolerado: Identificacao automatica do ponto de queda de performance (reducao de carga ou aumento excessivo de RPE para o mesmo volume).

3. Endpoint de Report de Estado:
   - Criacao do endpoint 'GET /api/v1/state/{user_id}' que consolida todas as metricas acima em um objeto JSON para consumo pelo modulo de IA.

---

## Fase 3: Orquestracao de IA e Geracao Adaptativa
Integracao com o servico Ollama para transformar o estado do usuario em prescricao de treinamento.

1. Integracao com Ollama:
   - Configuracao do cliente de comunicacao assincrona para a API do Ollama (rodando via Docker).
   - Selecao e configuracao do modelo base (Llama 3 ou Mistral).

2. Engenharia de Prompt e Geracao:
   - Desenvolvimento do 'Prompt Generator': Componente que recebe os dados do Perfil (Fase 1) e o Estado Consolidado (Fase 2) e monta o contexto para o LLM.
   - Estruturacao do 'System Prompt' para garantir que a IA responda estritamente no formato JSON definido no schema 'microcycle.py'.
   - Implementacao do endpoint 'POST /api/v1/generate-microcycle' que dispara o processo e persiste o resultado no banco de dados.

---

## Fase 4: Validacao de Seguranca e Finalizacao da API
Implementacao de filtros de seguranca pos-IA e exposicao dos endpoints finais para o frontend.

1. Camada de Validacao (Safety Caps):
   - Implementacao de filtros de seguranca para limitar o volume maximo semanal por grupo muscular, independente da sugestao da IA.
   - Logica de 'Deload Automatico': Se os indicadores de fadiga central ou estresse estiverem acima de um limiar critico, o sistema deve ignorar a progressao de carga e forçar uma semana de recuperacao.
   - Ajuste de RPE cap com base na qualidade do sono e estresse relatados nos check-ins.

2. Conclusao dos Endpoints de Sessao:
   - Endpoint para registro de logs de treino executados.
   - Endpoint para consulta de historico e evolucao de carga.
   - Garantia de conformidade total com os contratos definidos nos schemas do backend.
