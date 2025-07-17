# Technical Specification – Master Plan v5.0

## 1. Executive Summary

This specification defines the architecture and implementation plan for the Python C2S Challenge, focusing on the adoption of Anthropic's **Model Context Protocol (MCP)**. The solution will consist of a fully containerized AI ecosystem, orchestrated via Docker Compose, comprising three main services:

1.  **Database (`db`):** PostgreSQL 18, with a schema optimized for complex queries and performance.
2.  **MCP Server(s) (`server`):** A Python/FastAPI application exposing a set of tools for vehicle queries, following the MCP JSON-RPC 2.0 specification.
3.  **Conversational Client (`client`):** An interactive terminal application acting as the AI Agent host, orchestrating communication between the user, a configurable Language Model (LLM), and the available MCP Servers.

The design prioritizes **modularity, robustness, testability, and a "zero-effort" evaluation experience**, where the entire stack can be configured and run with minimal Docker commands.

## 2. Solution Architecture

The architecture follows a decoupled microservices pattern, with standardized communication via MCP.

1.  The **User** interacts with the **Client (`client`)** in the terminal.
2.  The **Client**, acting as the AI Agent host, manages the conversation and state. It dynamically discovers the tools available on the configured MCP Servers.
3.  The **Client** sends the dialogue and tool definitions to an external **LLM** (OpenAI, Google, etc.).
4.  The **LLM** plans the next action. It can:
    a. Ask a follow-up question to the user.
    b. Call one of the tools exposed by the MCP Servers.
5.  If a tool is called, the **Client** sends a **JSON-RPC 2.0** request to the appropriate **MCP Server (`server`)**.
6.  The **MCP Server** receives the call, validates it, and translates it into an **SQL** query for the **Database (`db`)**.
7.  The **Database** executes the query and returns the data.
8.  The **MCP Server** formats the data and sends the JSON-RPC response back to the **Client**.
9.  The **Client** sends the tool result back to the **LLM**, which then formulates a final natural language response for the user.

## 3. Database: PostgreSQL 18

**Goal:** Implement a performant and robust data foundation.

*   **Version:** PostgreSQL 18 (mandatory, for native `gen_random_uuid_v7()` support).
*   **Primary Key:** `id UUID` with `DEFAULT gen_random_uuid_v7()`, ensuring nearly-sequential IDs for efficient `INSERT` performance and pagination.
*   **Full-Text Search:** A `ts_search TSVECTOR` column, automatically generated and indexed with `GIN` for fast, efficient text searches with Portuguese language support.
*   **Schema DDL (`/docker/postgres/init/01-init-schema.sql`):**
    ```sql
    CREATE EXTENSION IF NOT EXISTS unaccent;

    CREATE TABLE IF NOT EXISTS veiculo (
        id UUID PRIMARY KEY DEFAULT uuidv7(),
        marca VARCHAR(100) NOT NULL,
        modelo VARCHAR(100) NOT NULL,
        ano_fabricacao INT NOT NULL,
        ano_modelo INT NOT NULL,
        motorizacao NUMERIC(2, 1) NOT NULL,
        tipo_combustivel VARCHAR(50) NOT NULL,
        cor VARCHAR(50) NOT NULL,
        quilometragem INT NOT NULL CHECK (quilometragem >= 0),
        numero_portas INT NOT NULL CHECK (numero_portas IN (2, 3, 4, 5)),
        tipo_transmissao VARCHAR(50) NOT NULL,
        preco NUMERIC(10, 2) NOT NULL CHECK (preco > 0),
        data_criacao TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
        ts_search TSVECTOR,
        CONSTRAINT ano_valido CHECK (ano_fabricacao >= 1990 AND ano_modelo >= ano_fabricacao AND ano_modelo <= EXTRACT(YEAR FROM now()) + 1)
    );

    CREATE OR REPLACE FUNCTION veiculo_tsvector_trigger() RETURNS trigger AS $$
    BEGIN
      NEW.ts_search := to_tsvector('portuguese', unaccent(NEW.marca) || ' ' || unaccent(NEW.modelo) || ' ' || unaccent(NEW.cor) || ' ' || unaccent(NEW.tipo_combustivel));
      RETURN NEW;
    END
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON veiculo FOR EACH ROW EXECUTE FUNCTION veiculo_tsvector_trigger();

    CREATE INDEX IF NOT EXISTS idx_veiculo_marca_modelo ON veiculo (marca, modelo);
    CREATE INDEX IF NOT EXISTS idx_veiculo_ano_fabricacao ON veiculo (ano_fabricacao DESC);
    CREATE INDEX IF NOT EXISTS idx_veiculo_preco ON veiculo (preco);
    CREATE INDEX IF NOT EXISTS idx_veiculo_ts_search ON veiculo USING GIN(ts_search);
    ```

## 4. Initial Data Load

**Goal:** Populate the database with a diverse and realistic dataset via a procedural script.

*   **Generation Script (`scripts/generate_inserts.py`):**
    ```python
    # scripts/generate_inserts.py
    import random
    import math
    from faker import Faker
    from rich.progress import track
    from pathlib import Path

    fake = Faker('pt_BR')
    Faker.seed(42)
    random.seed(42)

    NUM_VEHICLES = 250
    CURRENT_YEAR = 2025
    OUTPUT_DIR = Path(__file__).parent.parent / "docker" / "postgres" / "init"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE = OUTPUT_DIR / "02-populate-data.sql"

    # Dados realistas do mercado brasileiro
    brands_models = {
        'Ford': ['Ka', 'Fiesta', 'Focus', 'EcoSport', 'Ranger'], 'Chevrolet': ['Onix', 'Prisma', 'Cruze', 'S10', 'Tracker'],
        'Volkswagen': ['Gol', 'Polo', 'Virtus', 'T-Cross', 'Nivus', 'Saveiro'], 'Toyota': ['Corolla', 'Hilux', 'Yaris', 'RAV4'],
        'Honda': ['Civic', 'Fit', 'HR-V', 'WR-V', 'City'], 'Fiat': ['Mobi', 'Argo', 'Toro', 'Strada', 'Pulse'],
        'Hyundai': ['HB20', 'Creta', 'HB20S'], 'Jeep': ['Renegade', 'Compass', 'Commander'],
        'Renault': ['Kwid', 'Sandero', 'Logan', 'Duster', 'Captur']
    }
    fuel_types = ['Flex', 'Gasolina', 'Diesel', 'Etanol', 'Híbrido']
    transmission_types = ['Manual', 'Automática', 'CVT', 'Automatizada']
    popular_colors = ['Preto', 'Branco', 'Prata', 'Cinza', 'Vermelho', 'Azul']
    doors = [2, 4]
    engine_sizes = [1.0, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0]

    def generate_price_and_km(year):
        age = CURRENT_YEAR - year
        base_price = 120000 * math.exp(-age * 0.15)
        final_price = random.uniform(base_price * 0.8, base_price * 1.2)
        base_km = age * 15000
        final_km = max(0, random.uniform(base_km * 0.7, base_km * 1.3))
        return round(final_price, 2), int(final_km)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("INSERT INTO veiculo (marca, modelo, ano_fabricacao, ano_modelo, motorizacao, tipo_combustivel, cor, quilometragem, numero_portas, tipo_transmissao, preco) VALUES\n")
        values = []
        for _ in track(range(NUM_VEHICLES), description="Gerando dados de veículos..."):
            brand = random.choice(list(brands_models.keys()))
            model = random.choice(brands_models[brand])
            year_manufacture = random.randint(2010, CURRENT_YEAR - 1)
            year_model = random.choice([year_manufacture, year_manufacture + 1])
            price, km = generate_price_and_km(year_manufacture)

            values.append(
                f"('{brand}', '{model}', {year_manufacture}, {year_model}, "
                f"{random.choice(engine_sizes)}, '{random.choice(fuel_types)}', "
                f"'{random.choice(popular_colors)}', {km}, {random.choice(doors)}, "
                f"'{random.choice(transmission_types)}', {price})"
            )
        f.write(',\n'.join(values) + ';\n')

    print(f"\nFile {OUTPUT_FILE} generated successfully.")
    ```

## 5. MCP Server: FastAPI and `modelcontextprotocol` SDK

**Goal:** Implement the gateway exposing system functionalities to the AI world, following the MCP standard.

*   **Framework:** FastAPI, running on Uvicorn in async mode.
*   **SDK:** `modelcontextprotocol` (official Python package).
*   **Endpoint:** The MCP server will be mounted at a single endpoint, `/mcp`, handling all JSON-RPC calls.

### Tool Catalog:

1.  **`buscar_veiculos` (Main Tool):**
    *   **Description:** Searches vehicles in the database with a complex set of filters.
    *   **Parameters:** `VehicleFilter` object (with `search_text`, `brand`, `model`, `year_min/max`, `price_min/max`, etc.).
    *   **Return:** `List[VehicleResult]`.

2.  **`listar_marcas` (Support Tool):**
    *   **Description:** Returns a list of all unique vehicle brands available.
    *   **Return:** `List[str]`.

3.  **`listar_modelos` (Support Tool):**
    *   **Description:** Returns vehicle models. If brands are provided, filters by them.
    *   **Parameters:** `brands: Optional[List[str]] = None`.
    *   **Return:** `List[str]`.

4.  **`obter_range_anos` (Support Tool):**
    *   **Description:** Returns the minimum and maximum manufacturing years of available vehicles.
    *   **Return:** `{"min_year": int, "max_year": int}`.

5.  **`obter_range_precos` (Support Tool):**
    *   **Description:** Returns the minimum and maximum prices of available vehicles.
    *   **Return:** `{"min_price": float, "max_price": float}`.

6.  **Other Support Tools:** Will be implemented similarly: `obter_range_km`, `listar_cores_disponiveis`, `listar_tipos_combustivel`, `listar_tipos_transmissao`, `listar_numero_de_portas`.

## 6. MCP Client and Conversational Agent

**Goal:** Create a smart and robust CLI orchestrating the AI flow.

*   **Dynamic MCP Server Loading:** The client will read the `MCP_SERVERS` environment variable, which may contain one or more server definitions (one per line). For each line, the client will attempt to connect and discover its tools. Server connection failures will not interrupt the application, only generate a warning.
*   **LLM Abstraction:** A `LanguageModelService` class will be the interface, with concrete implementations selected by the `LLM_PROVIDER` variable.
*   **CLI UX:** The interface will use `rich` for formatted output and progress indicators, and `Python Prompt Toolkit` for user input.

## 7. Prompt Engineering and Agent Behavior

**Goal:** Clearly and robustly instruct the LLM for predictable and useful behavior.

### Base System Prompt

```
You are Car-Pal, a friendly, proactive, and extremely precise car sales assistant. Your main goal is to help users find the perfect vehicle in our inventory, using a set of internal tools.

<behavior_rules>
1.  **Be Proactive, Not Passive:** Don't wait for the user to provide all details. Guide the conversation. If the user is vague (e.g., "I want a good car"), use support tools (`listar_marcas`, `obter_range_precos`) to suggest options and refine the search.
2.  **Never Make Up Information:** You have no knowledge about the car inventory. All information about vehicles MUST be obtained exclusively through the provided tools. If a tool returns no results, inform the user that nothing was found with those criteria.
3.  **Use Support Tools First:** Before using the main tool `buscar_veiculos`, use auxiliary tools (`listar_marcas`, `listar_modelos`, etc.) to validate and refine the user's query. This avoids empty searches and improves the experience.
4.  **Format Results as Tables:** When presenting a list of vehicles, always format the output as a clear and readable Markdown table, highlighting the most important fields.
5.  **Think Step by Step:** Before each response, use the <thinking> block to outline your plan.
</behavior_rules>

<reasoning_process>
Strictly follow this mental process for each interaction:
1.  **Analyze:** Analyze the user's last message and the conversation history.
2.  **Plan:** Decide the next action. Do I need more information? If so, which support tool would help? Do I already have enough information for a main search?
3.  **Execute:** Choose the appropriate tool to execute.
4.  **Respond:** Based on the tool's results, formulate the response to the user.
</reasoning_process>

<examples>
<example>
<conversation>
User: Hi, I'm looking for a car.
</conversation>
<thinking>
The user was very vague. I need to understand what kind of car they want. I'll start by asking about the brands we have available. For this, I'll use the `listar_marcas` tool.
</thinking>
<tool_call>
{ "name": "listar_marcas", "input": {} }
</tool_call>
</example>
<example>
<conversation>
User: I like VW. I want a model up to 80k, newer.
</conversation>
<thinking>
The user specified the brand (Volkswagen), a price range (up to R$ 80,000), and a year range ("newer"). I have enough information for a main search. I'll call the `buscar_veiculos` tool with parameters `brand='Volkswagen'`, `year_min=2020`, `price_max=80000`.
</thinking>
<tool_call>
{ "name": "buscar_veiculos", "input": { "brand": "Volkswagen", "year_min": 2020, "price_max": 80000 } }
</tool_call>
</example>
</examples>

Below are the tools you can use. Call them when necessary.
```

## 8. Containerization and Orchestration (Docker Compose)

**Goal:** Ensure a fully automated setup and evaluation experience.

*   **`docker-compose.yml`:** Will orchestrate the `db`, `server`, and `client` services.
*   **`.env.example` (Configuration File):**

    ```ini
    # .env.example

    # --- Database Configuration ---
    POSTGRES_USER=admin
    POSTGRES_PASSWORD=secret
    POSTGRES_DB=veiculos_db
    DATABASE_URL=postgresql+asyncpg://admin:secret@db:5432/veiculos_db

    # --- Agent and LLM Configuration ---
    # LLM provider. Options: OPENAI, GOOGLE, DEEPSEEK
    LLM_PROVIDER=OPENAI
    # Specific model to use.
    # Examples: gpt-4o, gemini-1.5-pro-latest, deepseek-chat
    LLM_MODEL=gpt-4o

    # --- API Keys (fill only for the chosen provider) ---
    OPENAI_API_KEY=sk-...
    GOOGLE_API_KEY=...
    DEEPSEEK_API_KEY=sk-...

    # --- MCP Servers Configuration ---
    # List the MCP servers the client should connect to, one per line.
    # Format: TRANSPORT_TYPE,ADDRESS_OR_COMMAND
    MCP_SERVERS="SSE,http://server:8000/mcp"
    ```

## 9. Testing Strategy

*   **Unit Tests:** Focus on pure logic of tools and utility functions.
*   **Integration Tests (Server):** Using FastAPI's `TestClient`, will test all MCP server JSON-RPC endpoints, validating business logic and SQL queries.
*   **End-to-End Tests (Simulated):** Will simulate a full conversation, mocking the LLM with `pytest.monkeypatch` to validate the interaction flow between client and server, including failure scenarios.

## 10. Documentation and Delivery (`README.md`)

The `README.md` will be the complete guide for the evaluator, containing:
1.  **Overview and Architecture:** With embedded diagrams.
2.  **One-Click Setup:** Instructions on how to clone, create the `.env`, and run `docker-compose up`.
3.  **How to Use:** Instructions on how to run the client (`docker-compose run --rm client`) and the tests.
4.  **Design Decisions:** A section explaining key architectural choices.
5.  **Prompt Engineering:** A summary of the prompt strategy and agent behavior.

---

# Especificação Técnica – Master Plan v5.0

### 1. Sumário Executivo

Esta especificação define a arquitetura e o plano de implementação para o Desafio Python C2S, com foco na adoção do **Model Context Protocol (MCP)** da Anthropic. A solução consistirá em um ecossistema de IA totalmente containerizado, orquestrado via Docker Compose, composto por três serviços principais:

1.  **Banco de Dados (`db`):** PostgreSQL 18, com um esquema otimizado para buscas complexas e performance.
2.  **Servidor(es) MCP (`server`):** Uma aplicação Python/FastAPI que expõe um conjunto de ferramentas (tools) para consulta de veículos, seguindo a especificação JSON-RPC 2.0 do MCP.
3.  **Cliente Conversacional (`client`):** Uma aplicação de terminal interativa que atua como o host do Agente de IA, orquestrando a comunicação entre o usuário, um Modelo de Linguagem (LLM) configurável e os Servidores MCP disponíveis.

O design prioriza **modularidade, robustez, testabilidade e uma experiência de avaliação "zero-esforço"**, onde toda a stack pode ser configurada e executada com comandos mínimos do Docker.

### 2. Arquitetura Geral da Solução

A arquitetura segue um padrão de microsserviços desacoplados, com comunicação padronizada via MCP.

1.  **Usuário** interage com o **Cliente (`client`)** no terminal.
2.  O **Cliente**, atuando como host do Agente de IA, gerencia a conversa e o estado. Ele descobre dinamicamente as ferramentas disponíveis nos Servidores MCP configurados.
3.  O **Cliente** envia o diálogo e a definição das ferramentas para um **LLM** externo (OpenAI, Google, etc.).
4.  O **LLM** planeja a próxima ação. Ele pode:
    a. Fazer uma pergunta de volta ao usuário.
    b. Chamar uma das ferramentas expostas pelos Servidores MCP.
5.  Se uma ferramenta é chamada, o **Cliente** envia uma requisição **JSON-RPC 2.0** para o **Servidor MCP (`server`)** apropriado.
6.  O **Servidor MCP** recebe a chamada, a valida, e a traduz em uma consulta **SQL** para o **Banco de Dados (`db`)**.
7.  O **Banco de Dados** executa a consulta e retorna os dados.
8.  O **Servidor MCP** formata os dados e envia a resposta JSON-RPC de volta ao **Cliente**.
9.  O **Cliente** envia o resultado da ferramenta de volta ao **LLM**, que então formula uma resposta final em linguagem natural para o usuário.

### 3. Banco de Dados: PostgreSQL 18

**Objetivo:** Implementar uma fundação de dados performática e robusta.

*   **Versão:** PostgreSQL 18 (mandatório, para uso do `gen_random_uuid_v7()` nativo).
*   **Chave Primária:** `id UUID` com `DEFAULT gen_random_uuid_v7()`, garantindo IDs quase-sequenciais para performance de `INSERT` e paginação eficiente.
*   **Busca Textual:** Uma coluna `ts_search TSVECTOR` gerada automaticamente e indexada com `GIN` para buscas textuais rápidas, eficientes e com suporte à língua portuguesa.
*   **Schema DDL (`/docker/postgres/init/01-init-schema.sql`):**
    ```sql
    CREATE EXTENSION IF NOT EXISTS unaccent;

    CREATE TABLE IF NOT EXISTS veiculo (
        id UUID PRIMARY KEY DEFAULT uuidv7(),
        marca VARCHAR(100) NOT NULL,
        modelo VARCHAR(100) NOT NULL,
        ano_fabricacao INT NOT NULL,
        ano_modelo INT NOT NULL,
        motorizacao NUMERIC(2, 1) NOT NULL,
        tipo_combustivel VARCHAR(50) NOT NULL,
        cor VARCHAR(50) NOT NULL,
        quilometragem INT NOT NULL CHECK (quilometragem >= 0),
        numero_portas INT NOT NULL CHECK (numero_portas IN (2, 3, 4, 5)),
        tipo_transmissao VARCHAR(50) NOT NULL,
        preco NUMERIC(10, 2) NOT NULL CHECK (preco > 0),
        data_criacao TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
        ts_search TSVECTOR,
        CONSTRAINT ano_valido CHECK (ano_fabricacao >= 1990 AND ano_modelo >= ano_fabricacao AND ano_modelo <= EXTRACT(YEAR FROM now()) + 1)
    );

    CREATE OR REPLACE FUNCTION veiculo_tsvector_trigger() RETURNS trigger AS $$
    BEGIN
      NEW.ts_search := to_tsvector('portuguese', unaccent(NEW.marca) || ' ' || unaccent(NEW.modelo) || ' ' || unaccent(NEW.cor) || ' ' || unaccent(NEW.tipo_combustivel));
      RETURN NEW;
    END
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON veiculo FOR EACH ROW EXECUTE FUNCTION veiculo_tsvector_trigger();

    CREATE INDEX IF NOT EXISTS idx_veiculo_marca_modelo ON veiculo (marca, modelo);
    CREATE INDEX IF NOT EXISTS idx_veiculo_ano_fabricacao ON veiculo (ano_fabricacao DESC);
    CREATE INDEX IF NOT EXISTS idx_veiculo_preco ON veiculo (preco);
    CREATE INDEX IF NOT EXISTS idx_veiculo_ts_search ON veiculo USING GIN(ts_search);
    ```

### 4. Carga de Dados Inicial

**Objetivo:** Popular o banco de dados com um dataset diverso e realista através de um script procedural.

*   **Script de Geração (`scripts/generate_inserts.py`):**
    ```python
    # scripts/generate_inserts.py
    import random
    import math
    from faker import Faker
    from rich.progress import track
    from pathlib import Path

    fake = Faker('pt_BR')
    Faker.seed(42)
    random.seed(42)

    NUM_VEICULOS = 250
    CURRENT_YEAR = 2025
    OUTPUT_DIR = Path(__file__).parent.parent / "docker" / "postgres" / "init"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE = OUTPUT_DIR / "02-populate-data.sql"

    # Dados realistas do mercado brasileiro
    brands_models = {
        'Ford': ['Ka', 'Fiesta', 'Focus', 'EcoSport', 'Ranger'], 'Chevrolet': ['Onix', 'Prisma', 'Cruze', 'S10', 'Tracker'],
        'Volkswagen': ['Gol', 'Polo', 'Virtus', 'T-Cross', 'Nivus', 'Saveiro'], 'Toyota': ['Corolla', 'Hilux', 'Yaris', 'RAV4'],
        'Honda': ['Civic', 'Fit', 'HR-V', 'WR-V', 'City'], 'Fiat': ['Mobi', 'Argo', 'Toro', 'Strada', 'Pulse'],
        'Hyundai': ['HB20', 'Creta', 'HB20S'], 'Jeep': ['Renegade', 'Compass', 'Commander'],
        'Renault': ['Kwid', 'Sandero', 'Logan', 'Duster', 'Captur']
    }
    fuel_types = ['Flex', 'Gasolina', 'Diesel', 'Etanol', 'Híbrido']
    transmission_types = ['Manual', 'Automática', 'CVT', 'Automatizada']
    popular_colors = ['Preto', 'Branco', 'Prata', 'Cinza', 'Vermelho', 'Azul']
    doors = [2, 4]
    engine_sizes = [1.0, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0]

    def generate_price_and_km(year):
        age = CURRENT_YEAR - year
        base_price = 120000 * math.exp(-age * 0.15)
        final_price = random.uniform(base_price * 0.8, base_price * 1.2)
        base_km = age * 15000
        final_km = max(0, random.uniform(base_km * 0.7, base_km * 1.3))
        return round(final_price, 2), int(final_km)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("INSERT INTO veiculo (marca, modelo, ano_fabricacao, ano_modelo, motorizacao, tipo_combustivel, cor, quilometragem, numero_portas, tipo_transmissao, preco) VALUES\n")
        values = []
        for _ in track(range(NUM_VEICULOS), description="Gerando dados de veículos..."):
            brand = random.choice(list(brands_models.keys()))
            model = random.choice(brands_models[brand])
            year_manufacture = random.randint(2010, CURRENT_YEAR - 1)
            year_model = random.choice([year_manufacture, year_manufacture + 1])
            price, km = generate_price_and_km(year_manufacture)

            values.append(
                f"('{brand}', '{model}', {year_manufacture}, {year_model}, "
                f"{random.choice(engine_sizes)}, '{random.choice(fuel_types)}', "
                f"'{random.choice(popular_colors)}', {km}, {random.choice(doors)}, "
                f"'{random.choice(transmission_types)}', {price})"
            )
        f.write(',\n'.join(values) + ';\n')

    print(f"\nArquivo {OUTPUT_FILE} gerado com sucesso.")
    ```

### 5. Servidor MCP: FastAPI e SDK `modelcontextprotocol`

**Objetivo:** Implementar o gateway que expõe as funcionalidades do sistema ao mundo da IA, seguindo o padrão MCP.

*   **Framework:** FastAPI, rodando sobre Uvicorn em modo assíncrono.
*   **SDK:** `modelcontextprotocol` (pacote Python oficial).
*   **Endpoint:** O servidor MCP será montado em um único endpoint, `/mcp`, que lidará com todas as chamadas JSON-RPC.

#### Catálogo de Ferramentas (Tools):

1.  **`buscar_veiculos` (Ferramenta Principal):**
    *   **Descrição:** Busca veículos no banco de dados com um conjunto complexo de filtros.
    *   **Parâmetros:** Objeto `FiltroVeiculo` (com `texto_busca`, `marca`, `modelo`, `ano_min/max`, `preco_min/max`, etc.).
    *   **Retorno:** `List[VeiculoResultado]`.

2.  **`listar_marcas` (Ferramenta de Suporte):**
    *   **Descrição:** Retorna uma lista de todas as marcas de veículos únicas disponíveis.
    *   **Retorno:** `List[str]`.

3.  **`listar_modelos` (Ferramenta de Suporte):**
    *   **Descrição:** Retorna modelos de veículos. Se marcas forem fornecidas, filtra por elas.
    *   **Parâmetros:** `marcas: Optional[List[str]] = None`.
    *   **Retorno:** `List[str]`.

4.  **`obter_range_anos` (Ferramenta de Suporte):**
    *   **Descrição:** Retorna o ano de fabricação mínimo e máximo dos veículos disponíveis.
    *   **Retorno:** `{"ano_minimo": int, "ano_maximo": int}`.

5.  **`obter_range_precos` (Ferramenta de Suporte):**
    *   **Descrição:** Retorna o preço mínimo e máximo dos veículos disponíveis.
    *   **Retorno:** `{"preco_minimo": float, "preco_maximo": float}`.

6.  **Outras Ferramentas de Suporte:** Serão implementadas de forma similar: `obter_range_km`, `listar_cores_disponiveis`, `listar_tipos_combustivel`, `listar_tipos_transmissao`, `listar_numero_de_portas`.

### 6. Cliente MCP e Agente Conversacional

**Objetivo:** Criar uma CLI inteligente e robusta que orquestre o fluxo de IA.

*   **Carregamento Dinâmico de Servidores MCP:** O cliente lerá a variável de ambiente `MCP_SERVERS`, que pode conter uma ou mais definições de servidores (um por linha). Para cada linha, o cliente tentará conectar e descobrir suas ferramentas. Falhas na conexão de um servidor não interromperão a aplicação, apenas gerarão um aviso.
*   **Abstração de LLM:** Uma classe `LanguageModelService` será a interface, com implementações concretas selecionadas pela variável `LLM_PROVIDER`.
*   **UX da CLI:** A interface usará `rich` para saídas formatadas e indicadores de progresso, e `Python Prompt Toolkit` para entrada do usuário.

### 7. Engenharia de Prompt e Comportamento do Agente

**Objetivo:** Instruir o LLM de forma clara e robusta para um comportamento previsível e útil.

#### Prompt de Sistema Base

```
Você é o Car-Pal, um assistente especialista em vendas de carros, amigável, proativo e extremamente preciso. Seu objetivo principal é ajudar os usuários a encontrar o veículo perfeito em nosso inventário, utilizando um conjunto de ferramentas internas.

<regras_de_comportamento>
1.  **Seja Proativo, Não Passivo:** Não espere que o usuário forneça todos os detalhes. Guie a conversa. Se o usuário for vago (ex: "quero um carro bom"), use as ferramentas de suporte (`listar_marcas`, `obter_range_precos`) para sugerir opções e refinar a busca.
2.  **Nunca Invente Informações:** Você não tem conhecimento sobre o inventário de carros. Toda e qualquer informação sobre os veículos DEVE ser obtida exclusivamente através do uso das ferramentas fornecidas. Se uma ferramenta não retorna resultados, informe ao usuário que não encontrou nada com aqueles critérios.
3.  **Use Ferramentas de Suporte Primeiro:** Antes de usar a ferramenta principal `buscar_veiculos`, use as ferramentas auxiliares (`listar_marcas`, `listar_modelos`, etc.) para validar e refinar a consulta do usuário. Isso evita buscas vazias e melhora a experiência.
4.  **Formate Resultados em Tabelas:** Ao apresentar uma lista de veículos, sempre formate a saída como uma tabela Markdown clara e legível, destacando os campos mais importantes.
5.  **Pense Passo a Passo:** Antes de cada resposta, use o bloco <thinking> para delinear seu plano.
</regras_de_comportamento>

<processo_de_raciocinio>
Siga rigorosamente este processo mental para cada interação:
1.  **Analisar:** Analise a última mensagem do usuário e o histórico da conversa.
2.  **Planejar:** Decida a próxima ação. Preciso de mais informações? Se sim, qual ferramenta de suporte me ajudaria? Já tenho informações suficientes para uma busca principal?
3.  **Executar:** Escolha a ferramenta apropriada para executar.
4.  **Responder:** Com base nos resultados da ferramenta, formule a resposta para o usuário.
</processo_de_raciocinio>

<exemplos>
<exemplo>
<conversa>
Usuário: Oi, to procurando um carro.
</conversa>
<thinking>
O usuário foi muito vago. Preciso entender que tipo de carro ele quer. Vou começar perguntando sobre as marcas que temos disponíveis. Para isso, usarei a ferramenta `listar_marcas`.
</thinking>
<chamada_de_ferramenta>
{ "name": "listar_marcas", "input": {} }
</chamada_de_ferramenta>
</exemplo>
<exemplo>
<conversa>
Usuário: Gosto da VW. Queria um modelo até uns 80 mil, mais novo.
</conversa>
<thinking>
O usuário especificou a marca (Volkswagen), uma faixa de preço (até R$ 80.000) e uma faixa de ano ("mais novo"). Tenho informações suficientes para uma busca principal. Vou chamar a ferramenta `buscar_veiculos` com os parâmetros `marca='Volkswagen'`, `ano_min=2020`, `preco_max=80000`.
</thinking>
<chamada_de_ferramenta>
{ "name": "buscar_veiculos", "input": { "marca": "Volkswagen", "ano_min": 2020, "preco_max": 80000 } }
</chamada_de_ferramenta>
</exemplo>
</exemplos>

A seguir estão as ferramentas que você pode usar. Chame-as quando necessário.
```

### 8. Containerização e Orquestração (Docker Compose)

**Objetivo:** Garantir uma experiência de setup e avaliação totalmente automatizada.

*   **`docker-compose.yml`:** Orquestrará os serviços `db`, `server` e `client`.
*   **`.env.example` (Arquivo de Configuração):**

    ```ini
    # .env.example

    # --- Configuração do Banco de Dados ---
    POSTGRES_USER=admin
    POSTGRES_PASSWORD=secret
    POSTGRES_DB=veiculos_db
    DATABASE_URL=postgresql+asyncpg://admin:secret@db:5432/veiculos_db

    # --- Configuração do Agente e LLM ---
    # Provedor do LLM. Opções: OPENAI, GOOGLE, DEEPSEEK
    LLM_PROVIDER=OPENAI
    # Modelo específico do provedor a ser usado.
    # Exemplos: gpt-4o, gemini-1.5-pro-latest, deepseek-chat
    LLM_MODEL=gpt-4o

    # --- Chaves de API (preencha apenas a do provedor escolhido) ---
    OPENAI_API_KEY=sk-...
    GOOGLE_API_KEY=...
    DEEPSEEK_API_KEY=sk-...

    # --- Configuração dos Servidores MCP ---
    # Liste os servidores MCP que o cliente deve conectar, um por linha.
    # Formato: TIPO_TRANSPORTE,ENDERECO_OU_COMANDO
    MCP_SERVERS="SSE,http://server:8000/mcp"
    ```

### 9. Estratégia de Testes

*   **Testes Unitários:** Foco na lógica pura das ferramentas e funções utilitárias.
*   **Testes de Integração (Servidor):** Usando o `TestClient` do FastAPI, testará todos os endpoints JSON-RPC do servidor MCP, validando a lógica de negócio e as consultas SQL.
*   **Testes End-to-End (Simulados):** Simularão uma conversa completa, mockando o LLM com `pytest.monkeypatch` para validar o fluxo de interação entre cliente e servidor, incluindo cenários de falha.

### 10. Documentação e Entrega (`README.md`)

O `README.md` será o guia completo para o avaliador, contendo:
1.  **Visão Geral e Arquitetura:** Com diagramas incorporados.
2.  **Setup "One-Click":** Instruções sobre como clonar, criar o `.env` e rodar `docker-compose up`.
3.  **Como Usar:** Instruções sobre como executar o cliente (`docker-compose run --rm client`) e os testes.
4.  **Decisões de Design:** Uma seção explicando as escolhas arquiteturais chave.
5.  **Engenharia de Prompt:** Um resumo da estratégia de prompt e comportamento do agente.
