# Project Tasks & Roadmap

This document details all tasks required to deliver the Python Developer Challenge, covering business, technical, and delivery requirements. Tasks are organized by area, priority, and dependencies to guide the development from start to finish.

---

## 1. Infrastructure & Initial Setup
- [ ] **Create repository and directory structure**
    - `/docs`, `/scripts`, `/docker`, `/server`, `/client`, etc.
    - Acceptance criteria: Structure matches the master plan and is easy to navigate.
- [ ] **Configure Docker Compose**
    - Services: `db` (PostgreSQL 18), `server` (FastAPI), `client` (CLI)
    - `.env.example` with variables for database, LLM, MCP
    - Acceptance criteria: `docker-compose up` brings up the entire stack without manual intervention.

## 2. Data Modeling & Database
- [ ] **Define vehicle schema (min. 10 relevant attributes)**
    - Follow master plan DDL (UUID v7, constraints, tsvector, indexes)
    - Acceptance criteria: Schema ready for complex queries and text search.
- [ ] **Script for initial fake data load**
    - `scripts/generate_inserts.py` using Faker, 250 vehicles, realistic data
    - Acceptance criteria: Database is populated automatically when stack is up.
- [ ] **Test database integrity and performance**
    - Example queries, index checks
    - Acceptance criteria: Fast queries and no integrity errors.

## 3. Backend: MCP Server
- [ ] **Implement FastAPI server with `modelcontextprotocol` SDK**
    - Single endpoint `/mcp` (JSON-RPC 2.0)
    - Acceptance criteria: Server responds to valid MCP calls.
- [ ] **Implement MCP tools**
    - [ ] `buscar_veiculos` (main, with advanced filters)
    - [ ] `listar_marcas`, `listar_modelos`, `obter_range_anos`, `obter_range_precos`, etc.
    - Acceptance criteria: All tools work and return correct data.
- [ ] **Validation and error handling**
    - Acceptance criteria: MCP errors return clear and safe messages.

## 4. Frontend/CLI: MCP Client & Agent
- [ ] **Implement interactive CLI (Python, rich, prompt_toolkit)**
    - Dynamic discovery of MCP tools
    - Acceptance criteria: Robust CLI, smooth UX, no crashes.
- [ ] **LLM integration (provider abstraction)**
    - `LanguageModelService` class, support for OpenAI, Google, Deepseek
    - Acceptance criteria: Easy provider switch via `.env`.
- [ ] **Orchestrate conversational flow**
    - Prompt engineering as per master plan
    - Acceptance criteria: Agent follows proactivity rules, does not invent data, uses support tools before main tool.
- [ ] **Result formatting (Markdown/table)**
    - Acceptance criteria: Listings always in a clear table.

## 5. Testing (Unit, Integration, E2E)
- [ ] **Unit tests for pure logic (filters, utilities, etc.)**
    - Acceptance criteria: Minimum coverage of critical functions.
- [ ] **Integration tests for MCP server**
    - Use FastAPI TestClient, cover MCP endpoints
    - Acceptance criteria: All tools tested with valid and invalid cases.
- [ ] **End-to-end tests simulating full conversation**
    - LLM mock, client-server-db flow
    - Acceptance criteria: Simulation covers success and failure cases.

## 6. Documentation & Delivery
- [ ] **Update README.md with usage and architecture instructions**
    - Diagram, one-click setup, usage examples
    - Acceptance criteria: Any evaluator can run the project from scratch.
- [ ] **Document design decisions and prompt engineering**
    - Dedicated section in README/master_plan
    - Acceptance criteria: Clear justifications for technical choices.
- [ ] **Record demo video of the application**
    - Show different flows, search, error, etc.
    - Acceptance criteria: Video attached to the delivery.
- [ ] **Delivery checklist**
    - [ ] Public repository updated
    - [ ] Complete documentation
    - [ ] Video attached
    - [ ] Tests passing

---

# Tarefas & Roteiro do Projeto

Este documento detalha todas as tarefas necessárias para entregar o desafio Python Developer, cobrindo requisitos de negócio, técnicos e de entrega. As tasks estão organizadas por área, prioridade e dependências, para orientar o desenvolvimento do início ao fim do projeto.

---

## 1. Infraestrutura & Setup Inicial
- [ ] **Criar repositório e estrutura de diretórios**
    - `/docs`, `/scripts`, `/docker`, `/server`, `/client`, etc.
    - Critério de aceite: Estrutura compatível com o master plan e fácil navegação.
- [ ] **Configurar Docker Compose**
    - Serviços: `db` (PostgreSQL 18), `server` (FastAPI), `client` (CLI)
    - `.env.example` com variáveis para banco, LLM, MCP
    - Critério de aceite: `docker-compose up` sobe toda stack sem intervenção manual.

## 2. Modelagem de Dados & Banco
- [ ] **Definir schema do veículo (mín. 10 atributos relevantes)**
    - Seguir DDL do master plan (UUID v7, constraints, tsvector, índices)
    - Critério de aceite: Schema pronto para queries complexas e busca textual.
- [ ] **Script de carga inicial de dados fictícios**
    - `scripts/generate_inserts.py` usando Faker, 250 veículos, dados realistas
    - Critério de aceite: Banco populado automaticamente ao subir stack.
- [ ] **Testar integridade e performance do banco**
    - Consultas de exemplo, checagem de índices
    - Critério de aceite: Queries rápidas e sem erros de integridade.

## 3. Backend: Servidor MCP
- [ ] **Implementar servidor FastAPI com SDK `modelcontextprotocol`**
    - Endpoint único `/mcp` (JSON-RPC 2.0)
    - Critério de aceite: Servidor responde a chamadas MCP válidas.
- [ ] **Implementar ferramentas (tools) MCP**
    - [ ] `buscar_veiculos` (principal, com filtros avançados)
    - [ ] `listar_marcas`, `listar_modelos`, `obter_range_anos`, `obter_range_precos`, etc.
    - Critério de aceite: Todas as ferramentas funcionam e retornam dados corretos.
- [ ] **Validação e tratamento de erros**
    - Critério de aceite: Erros MCP retornam mensagens claras e seguras.

## 4. Frontend/CLI: Cliente MCP & Agente
- [ ] **Implementar CLI interativa (Python, rich, prompt_toolkit)**
    - Descoberta dinâmica de ferramentas MCP
    - Critério de aceite: CLI robusta, UX fluida, sem travamentos.
- [ ] **Integração com LLM (abstração por provider)**
    - Classe `LanguageModelService`, suporte a OpenAI, Google, Deepseek
    - Critério de aceite: Fácil troca de provider via `.env`.
- [ ] **Orquestração do fluxo conversacional**
    - Prompt engineering conforme master plan
    - Critério de aceite: Agente segue regras de proatividade, não inventa dados, usa ferramentas de suporte antes da principal.
- [ ] **Formatação de resultados (Markdown/tabela)**
    - Critério de aceite: Listagens sempre em tabela clara.

## 5. Testes (Unitários, Integração, E2E)
- [ ] **Testes unitários de lógica pura (filtros, utilitários, etc.)**
    - Critério de aceite: Cobertura mínima das funções críticas.
- [ ] **Testes de integração do servidor MCP**
    - Usar FastAPI TestClient, cobrir endpoints MCP
    - Critério de aceite: Todas as ferramentas testadas com casos válidos e inválidos.
- [ ] **Testes end-to-end simulando conversa completa**
    - Mock do LLM, fluxo client-server-db
    - Critério de aceite: Simulação cobre casos de sucesso e falha.

## 6. Documentação & Entrega
- [ ] **Atualizar README.md com instruções de uso e arquitetura**
    - Diagrama, setup one-click, exemplos de uso
    - Critério de aceite: Qualquer avaliador consegue rodar o projeto do zero.
- [ ] **Documentar decisões de design e prompt engineering**
    - Seção dedicada no README/master_plan
    - Critério de aceite: Justificativas claras para escolhas técnicas.
- [ ] **Gravar vídeo demo da aplicação**
    - Mostrar diferentes fluxos, busca, erro, etc.
    - Critério de aceite: Vídeo anexado na entrega.
- [ ] **Checklist de entrega**
    - [ ] Repositório público atualizado
    - [ ] Documentação completa
    - [ ] Vídeo anexado
    - [ ] Testes rodando
