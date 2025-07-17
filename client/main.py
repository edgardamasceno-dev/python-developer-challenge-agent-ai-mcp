from config import get_env
from mcp_client import get_mcp_clients
from llm import get_llm_service
from ui import print_status, print_error
from prompt_toolkit import PromptSession


def main():
    print_status("MCP client CLI is running")
    # Inicializa MCP clients
    mcp_clients = get_mcp_clients()
    if not mcp_clients:
        print_error("No MCP servers configured. Check MCP_SERVERS in your .env.")
        return
    print_status(f"Found {len(mcp_clients)} MCP server(s). Descobrindo tools...")
    # Descoberta dinâmica de tools (exemplo com o primeiro MCP server)
    import asyncio
    async def discover():
        await mcp_clients[0].list_tools()
    asyncio.run(discover())
    # Inicializa LLM provider
    llm = get_llm_service()
    print_status(f"LLM provider: {llm.provider}")
    # Loop principal da CLI
    session = PromptSession()
    while True:
        try:
            user_input = session.prompt('> ')
            if user_input.strip().lower() in {'exit', 'quit'}:
                print_status("Exiting MCP client CLI.")
                break
            # TODO: Orquestrar fluxo com LLM e MCP tools
            print_status(f"You said: {user_input}")
        except (KeyboardInterrupt, EOFError):
            print_status("Exiting MCP client CLI.")
            break

if __name__ == "__main__":
    main() 