"""
Configuração centralizada para a CLI MCP Client.
Carrega variáveis de ambiente do .env.
"""
from dotenv import load_dotenv
import os

load_dotenv()

def get_env(key, default=None):
    return os.getenv(key, default) 