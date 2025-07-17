import asyncio
import random
import time
import re
import json

from mcp_client import get_mcp_clients  # Seu client MCP
from llm import get_llm_service         # Seu wrapper de LLM
from ui import print_status, print_error
from prompt_toolkit import PromptSession

AGENT_NAMES = [
    "Eduardo", "Lucas", "Marina", "Paula", "Rafael", "Camila", "João", "Carla", "Bruno", "Ana"
]
AGENT_NAME = random.choice(AGENT_NAMES)

SYSTEM_PROMPT = f"""
Você é {AGENT_NAME}, um especialista em vendas de carros, amigável, proativo e extremamente preciso. Seu objetivo principal é ajudar os usuários a encontrar o veículo perfeito em nosso inventário, utilizando um conjunto de ferramentas internas que serão listadas para você.

<regras_de_comportamento>
1. Sempre responda em português do Brasil (pt-BR), de forma natural e profissional.
2. Para atender ao pedido do usuário, você DEVE usar as ferramentas disponíveis. Consulte a lista de ferramentas e suas descrições para escolher a mais adequada.
3. Nunca mencione ao usuário que você está usando ferramentas. Apenas apresente a informação como se fosse sua.
4. Seja proativo: se o usuário for vago, sugira opções e faça perguntas para refinar a busca.
5. Nunca invente informações: tudo deve ser obtido pelas ferramentas.
6. Ao apresentar uma lista de veículos, exiba todas as propriedades relevantes (UUID, marca, modelo, ano fabricação, ano modelo, motorização, tipo combustível, cor, km, portas, transmissão, preço), sempre com o UUID como primeiro campo.
7. Considere 'id' e 'uuid' como sinônimos. Se o usuário pedir o id de um veículo de uma lista, use o contexto da conversa para obter o UUID real daquele item.
8. Nunca use markdown ou emojis. Apenas texto puro.
9. Se o usuário pedir confirmação, valide a resposta anterior consultando a ferramenta apropriada novamente.
10. Você NUNCA deve responder perguntas sobre o inventário (marcas, modelos, cores, preços, etc.) sem antes consultar a ferramenta correspondente.
</regras_de_comportamento>

IMPORTANTE: Sempre que precisar consultar alguma informação, responda APENAS com um bloco <tool_call> em JSON, sem texto antes ou depois. Exemplo:
<tool_call>
{{
  "name": "nome_da_ferramenta",
  "input": {{
    "argumento1": "valor1",
    "argumento2": "valor2"
  }}
}}
</tool_call>
"""

last_vehicle_list = []

def parse_tool_call(llm_response):
    match = re.search(r'<tool_call>\s*({[\s\S]+?})\s*</tool_call>', llm_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception as e:
            print(f'[DEBUG] Erro ao parsear tool_call: {e}')
            return None
    match2 = re.search(r'({\s*"name"\s*:\s*"[^"]+".*?\})', llm_response, re.DOTALL)
    if match2:
        try:
            return json.loads(match2.group(1))
        except Exception:
            return None
    return None

def extract_final_response(llm_response):
    response = re.sub(r'<tool_call>[\s\S]*?</tool_call>', '', llm_response, flags=re.IGNORECASE)
    response = re.sub(r'{\s*"name"\s*:\s*"[^"]+".*?\}', '', response, flags=re.DOTALL)
    return response.strip()

def clean_llm_response(text):
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'(?i)(executando|buscando|consultando|verificando)[^\n\r]*[\n\r]?', '', text)
    return text.strip()

def stream_print(text, delay=0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

# --- FUNÇÃO CORRIGIDA ---
# Corrigido o SyntaxError e melhorada a formatação de números para o padrão pt-BR.
def print_vehicle_list_aligned(vehicles):
    global last_vehicle_list
    if not vehicles:
        print("Nenhum veículo encontrado com os critérios informados.")
        last_vehicle_list = []
        return
    last_vehicle_list = vehicles
    # Larguras ajustadas para acomodar a formatação de número e preço
    widths = {
        "uuid": 36, "brand": 12, "model": 12, "year_manufacture": 6, "year_model": 6,
        "engine": 6, "fuel_type": 10, "color": 10, "km": 9, "doors": 2, "transmission": 12, "price": 14
    }
    header = f"{'#':>2}. {'UUID':<{widths['uuid']}} | {'Marca':<{widths['brand']}} | {'Modelo':<{widths['model']}} | {'AnoF':>{widths['year_manufacture']}} | {'AnoM':>{widths['year_model']}} | {'Mot.':>{widths['engine']}} | {'Comb.':<{widths['fuel_type']}} | {'Cor':<{widths['color']}} | {'KM':>{widths['km']}} | {'P':>{widths['doors']}} | {'Transmissão':<{widths['transmission']}} | {'Preço':>{widths['price']}}"
    print(header)
    print('-' * len(header))
    for idx, v in enumerate(vehicles, 1):
        # Preparar variáveis de preço e km com tratamento de erro e formatação pt-BR
        try:
            price_val = float(v.get('price', 0.0))
            price_str_en = f"{price_val:,.2f}"
            price_str_br = "R$ " + price_str_en.replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            price_str_br = "R$ 0,00"

        try:
            km_val = int(v.get('km', 0))
            km_str = f"{km_val:,d}".replace(",", ".")
        except (ValueError, TypeError):
            km_str = "0"
            
        doors_str = str(v.get('doors', ''))

        # Construir a linha final com valores pré-formatados, evitando o SyntaxError
        line = (
            f"{idx:>2}. {v.get('id', ''):<{widths['uuid']}} | "
            f"{v.get('brand', ''):<{widths['brand']}} | "
            f"{v.get('model', ''):<{widths['model']}} | "
            f"{v.get('year_manufacture', ''):>{widths['year_manufacture']}} | "
            f"{v.get('year_model', ''):>{widths['year_model']}} | "
            f"{v.get('engine', ''):>{widths['engine']}} | "
            f"{v.get('fuel_type', ''):<{widths['fuel_type']}} | "
            f"{v.get('color', ''):<{widths['color']}} | "
            f"{km_str:>{widths['km']}} | "
            f"{doors_str:>{widths['doors']}} | "
            f"{v.get('transmission', ''):<{widths['transmission']}} | "
            f"{price_str_br:>{widths['price']}}"
        )
        print(line)

# --- FUNÇÃO CORRIGIDA ---
# Melhorada a formatação de preço para o padrão pt-BR.
def format_tool_result_for_user(tool_name, tool_result):
    """Formata o resultado da ferramenta para exibição ao usuário final."""
    if isinstance(tool_result, dict) and 'result' in tool_result:
        tool_result = tool_result['result']

    if tool_name == "buscar_veiculos":
        vehicles = tool_result if isinstance(tool_result, list) else []
        # Não exibir lista antes da LLM
        return f"Encontrei {len(vehicles)} veículo(s) com base na sua busca." if vehicles else "Não encontrei veículos com os critérios especificados."

    elif tool_name in ["listar_marcas", "listar_modelos", "listar_cores_disponiveis"]:
        items = tool_result if isinstance(tool_result, list) else []
        if not items: return "Não encontrei nenhuma opção disponível."
        noun = "marcas" if "marcas" in tool_name else "modelos" if "modelos" in tool_name else "cores"
        msg = f"As {noun} disponíveis são: {', '.join(items)}."
        return msg

    elif tool_name == "obter_range_anos":
        anos = tool_result if isinstance(tool_result, dict) else {}
        msg = f"Temos veículos fabricados entre {anos.get('min_year')} e {anos.get('max_year')}."
        return msg

    elif tool_name == "obter_range_precos":
        precos = tool_result if isinstance(tool_result, dict) else {}
        try:
            min_price = float(precos.get('min_price', 0.0))
            min_price_str = f"{min_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError): min_price_str = "0,00"
        try:
            max_price = float(precos.get('max_price', 0.0))
            max_price_str = f"{max_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError): max_price_str = "0,00"
        msg = f"Os preços dos nossos veículos variam de R$ {min_price_str} a R$ {max_price_str}."
        return msg
    
    # Não exibir resultado formatado cru
    return ""


def format_tool_result_for_llm(tool_name, tool_result):
    if tool_name == "buscar_veiculos":
        return json.dumps(tool_result, ensure_ascii=False)
    if isinstance(tool_result, dict) and 'result' in tool_result:
        return json.dumps(tool_result['result'], ensure_ascii=False)
    return json.dumps(tool_result, ensure_ascii=False)


def extract_vehicle_id_from_question(user_input):
    match = re.search(r'(?:id|uuid)\s*(?:do|da)?\s*(\d+)', user_input, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except (ValueError, IndexError):
            return None
    return None

def extract_color_from_question(user_input, cores_disponiveis):
    for cor in cores_disponiveis:
        if cor.lower() in user_input.lower():
            return cor
    match = re.search(r'cor\s+([a-zA-Zçãõáéíóúâêôàèìòùäëïöü]+)', user_input, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    return None

async def call_tool_with_retries(mcp_client, name, input_args, max_retries=3):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            result = await mcp_client.call_tool(name, input_args)
            return result, None
        except Exception as e:
            last_error = e
            print(f"[Erro] Falha ao executar tool '{name}' (tentativa {attempt}/{max_retries}): {e}")
            await asyncio.sleep(0.5)
    return None, last_error

async def show_intro_prompt(mcp_client):
    resp = await mcp_client.get_prompt("search_intro")
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_filters_summary_prompt(mcp_client, filters):
    resp = await mcp_client.get_prompt("filters_summary", {"filters": filters})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_search_result_summary_prompt(mcp_client, vehicle_count, min_price=None, max_price=None, min_km=None, max_km=None):
    args = {"vehicle_count": vehicle_count}
    if min_price is not None: args["min_price"] = min_price
    if max_price is not None: args["max_price"] = max_price
    if min_km is not None: args["min_km"] = min_km
    if max_km is not None: args["max_km"] = max_km
    resp = await mcp_client.get_prompt("search_result_summary", args)
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_no_results_prompt(mcp_client, filters):
    resp = await mcp_client.get_prompt("no_results", {"filters": filters})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_vehicle_details_prompt(mcp_client, vehicle):
    resp = await mcp_client.get_prompt("vehicle_details", {"vehicle": vehicle})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_suggest_more_filters_prompt(mcp_client, suggested_filters):
    resp = await mcp_client.get_prompt("suggest_more_filters", {"suggested_filters": suggested_filters})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_action_confirmation_prompt(mcp_client, action):
    resp = await mcp_client.get_prompt("action_confirmation", {"action": action})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_colors_list_prompt(mcp_client, colors):
    resp = await mcp_client.get_prompt("colors_list", {"colors": colors})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_colors_no_results_prompt(mcp_client):
    resp = await mcp_client.get_prompt("colors_no_results")
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_brands_list_prompt(mcp_client, brands):
    resp = await mcp_client.get_prompt("brands_list", {"brands": brands})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_brands_no_results_prompt(mcp_client):
    resp = await mcp_client.get_prompt("brands_no_results")
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_models_list_prompt(mcp_client, models):
    resp = await mcp_client.get_prompt("models_list", {"models": models})
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def show_models_no_results_prompt(mcp_client):
    resp = await mcp_client.get_prompt("models_no_results")
    messages = resp.get('result', {}).get('messages', [])
    if messages:
        print(messages[0]['content'])

async def main_async():
    global last_vehicle_list
    print_status("MCP client CLI is running")
    mcp_clients = get_mcp_clients()
    if not mcp_clients:
        print_error("No MCP servers configured. Check MCP_SERVERS in your .env.")
        return

    mcp_client = mcp_clients[0]
    print_status(f"Conectado a {mcp_client.server_url}. Descobrindo ferramentas...")

    try:
        await mcp_client.list_tools()
        tools = mcp_client.tools or []
        if not tools:
            print_error("Nenhuma ferramenta encontrada no MCP. Verifique o servidor MCP.")
            return
    except Exception as e:
        print_error(f"Falha ao descobrir ferramentas do MCP: {e}")
        return

    tool_defs = []
    for tool in tools:
        params = tool.get('parameters', {}).get('properties', {})
        param_defs = [f"  - {name} ({prop.get('type')}): {prop.get('description')}" for name, prop in params.items()]
        param_str = "\n".join(param_defs)
        tool_defs.append(f"Nome: {tool['name']}\nDescrição: {tool['description']}\nParâmetros:\n{param_str if param_str else '  Nenhum'}")
    tools_prompt_section = "Você tem acesso às seguintes ferramentas para consulta:\n<ferramentas>\n" + "\n\n".join(tool_defs) + "\n</ferramentas>"
    
    tool_names = ', '.join([t['name'] for t in tools])
    print_status(f"Ferramentas disponíveis para o agente: {tool_names}.")
    
    llm = get_llm_service()
    print_status(f"LLM provider: {llm.provider} | Model: {getattr(llm, 'model', 'desconhecido')}")
    
    session = PromptSession()
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    print_status(f"\nOlá! Meu nome é {AGENT_NAME} e estou aqui para ajudar você a encontrar o carro ideal.")

    while True:
        try:
            user_input = await session.prompt_async('> ')
            if user_input.strip().lower() in {'exit', 'quit'}:
                print_status("Saindo do MCP client CLI.")
                break

            idx = extract_vehicle_id_from_question(user_input)
            if idx is not None and last_vehicle_list:
                if 1 <= idx <= len(last_vehicle_list):
                    vehicle = last_vehicle_list[idx - 1]
                    uuid = vehicle.get("id") or vehicle.get("uuid")
                    stream_print(f"O ID do veículo {idx} ({vehicle.get('brand')} {vehicle.get('model')}) é: {uuid}")
                else:
                    stream_print("Não foi possível encontrar o veículo com este número na lista anterior.")
                continue

            conversation.append({"role": "user", "content": user_input})
            
            messages_for_llm = conversation.copy()
            messages_for_llm.append({"role": "system", "content": tools_prompt_section})

            llm_response = llm.chat(messages_for_llm)
            # print(f'[DEBUG LLM RAW] {llm_response}')

            tool_call = parse_tool_call(llm_response)
            if tool_call:
                # print(f'[DEBUG] Tool call parsed: {tool_call}')
                tool_result, tool_error = await call_tool_with_retries(mcp_client, tool_call['name'], tool_call.get('input', {}))
                
                if tool_result is not None:
                    # INTEGRAÇÃO DE PROMPTS DINÂMICOS PARA MARCAS, MODELOS E CORES
                    if tool_call['name'] == 'listar_marcas':
                        brands = tool_result['brands'] if isinstance(tool_result, dict) and 'brands' in tool_result else tool_result
                        if brands:
                            await show_brands_list_prompt(mcp_client, brands)
                        else:
                            await show_brands_no_results_prompt(mcp_client)
                    elif tool_call['name'] == 'listar_modelos':
                        models = tool_result['models'] if isinstance(tool_result, dict) and 'models' in tool_result else tool_result
                        if models:
                            await show_models_list_prompt(mcp_client, models)
                        else:
                            await show_models_no_results_prompt(mcp_client)
                    elif tool_call['name'] == 'listar_cores_disponiveis':
                        colors = tool_result['cores'] if isinstance(tool_result, dict) and 'cores' in tool_result else tool_result
                        if colors:
                            await show_colors_list_prompt(mcp_client, colors)
                        else:
                            await show_colors_no_results_prompt(mcp_client)
                        # Verificar se o usuário perguntou por uma cor específica
                        cor_perguntada = extract_color_from_question(user_input, colors if colors else [])
                        if cor_perguntada:
                            if cor_perguntada in colors:
                                print(f"A cor {cor_perguntada} está disponível em nosso inventário.")
                            else:
                                print(f"A cor {cor_perguntada} não está disponível em nosso inventário no momento.")
                    # FIM INTEGRAÇÃO
                    user_facing_msg = format_tool_result_for_user(tool_call['name'], tool_result)
                    llm_facing_content = format_tool_result_for_llm(tool_call['name'], tool_result)
                    
                    conversation.append({"role": "assistant", "content": str(llm_response or "")})
                    conversation.append({"role": "tool", "name": str(tool_call.get('name', '')), "content": str(llm_facing_content or "")})
                    
                    messages_for_summary = conversation.copy()
                    if tool_call['name'] == 'buscar_veiculos':
                        messages_for_summary.append({"role": "system", "content": "Resuma para o usuário a lista de veículos que foi encontrada e exibida. Pergunte se ele deseja mais detalhes sobre algum deles."})
                    
                    final_response_llm = llm.chat(messages_for_summary)
                    final_text = extract_final_response(final_response_llm)
                    final_text = clean_llm_response(final_text)
                    if final_text: stream_print(final_text)
                    conversation.append({"role": "assistant", "content": str(final_response_llm or "")})
                else:
                    error_message = f"Desculpe, ocorreu um erro ao tentar consultar a informação. Tente novamente."
                    if tool_error: print(f"Motivo: {tool_error}")
                    stream_print(error_message)
                    conversation.append({"role": "assistant", "content": str(error_message)})
            else:
                # print('[DEBUG] Nenhuma chamada de ferramenta detectada!')
                final_text = extract_final_response(llm_response)
                final_text = clean_llm_response(final_text)
                if final_text: stream_print(final_text)
                conversation.append({"role": "assistant", "content": str(llm_response or "")})

        except (KeyboardInterrupt, EOFError):
            print_status("\nSaindo do MCP client CLI.")
            break
        except Exception as e:
            print_error(f"Ocorreu um erro inesperado no loop principal: {e}")
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except (ImportError, KeyboardInterrupt, asyncio.CancelledError):
        print_status("Saindo do MCP client CLI.")