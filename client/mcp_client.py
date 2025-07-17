"""
Módulo para comunicação com servidores MCP (Model Context Protocol).
Inclui descoberta dinâmica de tools e chamada de tools via JSON-RPC.
"""
import os
import httpx
import json

class MCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.tools = []

    async def list_tools(self):
        """Descobre as tools disponíveis no servidor MCP."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.server_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            self.tools = data.get('result', {}).get('tools', [])
            return self.tools

    async def call_tool(self, name: str, arguments: dict, id: int = 2):
        """Chama uma tool MCP específica."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
            "id": id
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.server_url, json=payload)
            resp.raise_for_status()
            return resp.json()

def get_mcp_clients():
    """Lê MCP_SERVERS do .env e retorna instâncias de MCPClient."""
    servers = os.getenv('MCP_SERVERS', '').splitlines()
    return [MCPClient(url.split(',')[1].strip()) for url in servers if ',' in url] 