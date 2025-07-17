# Python Developer Technical Challenge - C2S

[English](#english) | [Português (BR)](#português-br)

---

# English

### Project Description

This repository contains the solution to the C2S Python Developer technical challenge.

The project features a terminal-based virtual agent designed to assist users in finding cars based on their specified criteria. Key components include data modeling for vehicles, populating a database with mock data, a client-server architecture implemented with the custom MCP (Model Context Protocol), and the integration of a Large Language Model (LLM) for natural language interaction.

For a detailed description of the challenge requirements, please see the document below:

*   **[Full Challenge Description](./docs/challenge.md#english)**
*   **[Technical Specification – Master Plan](./docs/master_plan.md#technical-specification--master-plan-v50)**

---

# Português (BR)

### Descrição do Projeto

Este repositório contém a solução para o desafio técnico de Desenvolvedor Python da C2S.

O projeto apresenta um agente virtual baseado em terminal, projetado para auxiliar os usuários a encontrar carros com base em seus critérios. Os componentes principais incluem a modelagem de dados para veículos, o preenchimento de um banco de dados com dados fictícios, uma arquitetura cliente-servidor implementada com o protocolo personalizado MCP (Model Context Protocol) e a integração de um Modelo de Linguagem Grande (LLM) para interação em linguagem natural.

Para uma descrição detalhada dos requisitos do desafio, consulte o documento abaixo:

*   **[Descrição Completa do Desafio](./docs/challenge.md#português-br)**
*   **[Especificação Técnica – Master Plan](./docs/master_plan.md#especificação-técnica--master-plan-v50)**

## Project Structure

The repository is organized as follows:

```
/
├── docs/           # Project documentation (master_plan, tasks, challenge, etc.)
├── scripts/        # Utility scripts (e.g., data generation, migrations)
├── docker/         # Docker and database configuration files
│   └── postgres/
│       └── init/   # SQL schema and initial data
├── server/         # FastAPI backend (MCP server)
├── client/         # CLI code (MCP client/agent)
├── docker-compose.yml
├── .env.example
├── README.md
```

Each directory contains a `.gitkeep` file or documentation to ensure it is versioned. See the `master_plan.md` for detailed architectural decisions.
