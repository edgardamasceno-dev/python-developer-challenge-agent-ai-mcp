from config import get_env
from mcp_client import get_mcp_clients
from llm import get_llm_service
from ui import print_status, print_error, print_markdown
from prompt_toolkit import PromptSession
import json
import time
import sys
import random

AGENT_NAMES = [
    "Eduardo", "Lucas", "Marina", "Paula", "Rafael", "Camila", "João", "Carla", "Bruno", "Ana"
]
AGENT_NAME = random.choice(AGENT_NAMES)

SYSTEM_PROMPT = f"""
Você é {AGENT_NAME}, um especialista em vendas de carros, amigável, proativo e extremamente preciso. Seu objetivo principal é ajudar os usuários a encontrar o veículo perfeito em nosso inventário, utilizando um conjunto de ferramentas internas.

<regras_de_comportamento>
1. Sempre responda em português do Brasil (pt-BR), de forma natural e profissional.
2. Nunca mencione ao usuário que está usando ferramentas internas, nem diga que está executando, buscando, consultando, etc. Apenas apresente a informação como se fosse sua.
3. Seja proativo: se o usuário for vago, sugira opções e faça perguntas para refinar a busca.
4. Nunca invente informações: tudo deve ser obtido pelas ferramentas internas.
5. Use ferramentas de suporte antes da principal, mas nunca mencione isso ao usuário.
6. Formate resultados de listas em tabela ou lista clara, mas nunca diga que está \"listando\" ou \"executando\".
7. Nunca use emojis.
</regras_de_comportamento>

<processo_de_raciocinio>
1. Analise a última mensagem do usuário e o histórico.
2. Decida a próxima ação. Precisa de mais informação? Já pode buscar veículos?
3. Se usar uma ferramenta, use a informação retornada para responder ao usuário de forma natural, SEM mencionar a ferramenta.
4. Responda ao usuário de forma clara, direta e em português.
</processo_de_raciocinio>
"""

def parse_tool_call(llm_response):
    """Extrai o bloco de chamada de tool em JSON da resposta do LLM."""
    import re
    match = re.search(r'\{\s*"name"\s*:\s*"[^"]+".*?\}', llm_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None

def extract_final_response(llm_response):
    """Remove blocos <thinking>, blocos de ação e retorna apenas a resposta final do agente."""
    import re
    # Remove blocos <thinking>...</thinking>
    response = re.sub(r'<thinking>[\s\S]*?</thinking>', '', llm_response, flags=re.IGNORECASE)
    # Remove blocos de ação (```action ...``` ou blocos JSON)
    response = re.sub(r'```action[\s\S]*?```', '', response, flags=re.IGNORECASE)
    response = re.sub(r'```json[\s\S]*?```', '', response, flags=re.IGNORECASE)
    # Remove blocos de código genéricos
    response = re.sub(r'```[\s\S]*?```', '', response)
    # Remove espaços extras
    return response.strip()

def clean_llm_response(text):
    import re
    # Remove blocos <execute=...>
    text = re.sub(r'<execute=.*?>', '', text)
    # Remove frases como "Executando...", "Buscando...", "Consultando..."
    text = re.sub(r'(?i)(executando|buscando|consultando|verificando)[^\n\r]*[\n\r]?', '', text)
    # Remove blocos de código e instruções
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove espaços extras
    return text.strip()

def stream_print(text, delay=0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def is_list_tool(tool_name):
    return tool_name in {"listar_marcas", "listar_modelos", "obter_range_anos", "obter_range_precos"}

def format_tool_result(tool_name, tool_result):
    from ui import print_table, print_markdown
    if tool_name == "listar_marcas":
        marcas = tool_result.get('result')
        if isinstance(marcas, dict) and 'marcas' in marcas:
            marcas = marcas['marcas']
        if isinstance(marcas, list):
            # Mensagem clara em português
            msg = f"As marcas disponíveis são: {', '.join(marcas)}."
            print(msg)
            print_table(["Marcas"], [[m] for m in marcas], title="Marcas disponíveis")
            return msg
        else:
            print_markdown(str(marcas))
            return str(marcas)
    elif tool_name == "listar_modelos":
        modelos = tool_result.get('result')
        if isinstance(modelos, dict) and 'modelos' in modelos:
            modelos = modelos['modelos']
        if isinstance(modelos, list):
            msg = f"Os modelos disponíveis são: {', '.join(modelos)}."
            print(msg)
            print_table(["Modelos"], [[m] for m in modelos], title="Modelos disponíveis")
            return msg
        else:
            print_markdown(str(modelos))
            return str(modelos)
    elif tool_name == "obter_range_anos":
        anos = tool_result.get('result')
        if isinstance(anos, dict):
            msg = f"Os veículos disponíveis vão de {anos.get('min_year')} até {anos.get('max_year')}."
            print(msg)
            print_table(["Ano Mínimo", "Ano Máximo"], [[anos.get('min_year'), anos.get('max_year')]], title="Faixa de Anos")
            return msg
        else:
            print_markdown(str(anos))
            return str(anos)
    elif tool_name == "obter_range_precos":
        precos = tool_result.get('result')
        if isinstance(precos, dict):
            msg = f"Os preços disponíveis vão de R$ {precos.get('min_price')} até R$ {precos.get('max_price')}."
            print(msg)
            print_table(["Preço Mínimo", "Preço Máximo"], [[precos.get('min_price'), precos.get('max_price')]], title="Faixa de Preços")
            return msg
        else:
            print_markdown(str(precos))
            return str(precos)
    else:
        print_markdown(str(tool_result))
        return str(tool_result)

def main():
    print_status("MCP client CLI is running")
    mcp_clients = get_mcp_clients()
    if not mcp_clients:
        print_error("No MCP servers configured. Check MCP_SERVERS in your .env.")
        return
    print_status(f"Found {len(mcp_clients)} MCP server(s). Descobrindo tools...")
    import asyncio
    async def discover():
        await mcp_clients[0].list_tools()
    asyncio.run(discover())
    llm = get_llm_service()
    # Exibe tools descobertas de forma amigável
    tools = mcp_clients[0].tools
    if tools:
        tool_names = ', '.join([t['name'].replace('_', ' ') for t in tools])
        print_status(f"Ferramentas disponíveis para o agente: {tool_names}.")
    print_status(f"LLM provider: {llm.provider}")
    session = PromptSession()
    conversation = []
    # Inicia com o system prompt
    conversation.append({"role": "system", "content": SYSTEM_PROMPT})
    print_status(f"Olá! Meu nome é {AGENT_NAME} e estou aqui para ajudar você a encontrar o carro ideal.")
    while True:
        try:
            user_input = session.prompt('> ')
            if user_input.strip().lower() in {'exit', 'quit'}:
                print_status("Exiting MCP client CLI.")
                break
            conversation.append({"role": "user", "content": user_input})
            # Monta contexto para o LLM
            messages = conversation.copy()
            # Adiciona tools disponíveis
            tools = mcp_clients[0].tools
            tool_defs = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
            messages.append({"role": "system", "content": f"Available tools:\n{tool_defs}"})
            # Chama o LLM
            llm_response = llm.chat(messages)
            if not llm_response:
                print_error("No response from LLM.")
                continue
            # Extrai e exibe apenas a resposta final do agente
            final_text = extract_final_response(llm_response)
            final_text = clean_llm_response(final_text)
            if final_text:
                stream_print(final_text)
            # Verifica se há chamada de tool
            tool_call = parse_tool_call(llm_response)
            if tool_call:
                async def call():
                    result = await mcp_clients[0].call_tool(tool_call['name'], tool_call.get('input', {}))
                    return result
                tool_result = asyncio.run(call())
                if is_list_tool(tool_call['name']):
                    tool_msg = format_tool_result(tool_call['name'], tool_result)
                    # Adiciona resultado da tool ao histórico como mensagem clara em pt-BR
                    conversation.append({"role": "tool", "name": tool_call['name'], "content": tool_msg})
                else:
                    conversation.append({"role": "tool", "name": tool_call['name'], "content": json.dumps(tool_result)})
                # Chama o LLM novamente para gerar resposta final
                messages = conversation.copy()
                final_response = llm.chat(messages)
                final_text2 = extract_final_response(final_response)
                final_text2 = clean_llm_response(final_text2)
                if final_text2:
                    stream_print(final_text2)
                conversation.append({"role": "assistant", "content": final_response})
            else:
                conversation.append({"role": "assistant", "content": llm_response})
        except (KeyboardInterrupt, EOFError):
            print_status("Exiting MCP client CLI.")
            break

if __name__ == "__main__":
    main() 