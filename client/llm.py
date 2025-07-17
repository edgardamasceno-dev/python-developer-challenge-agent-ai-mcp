"""
Abstração para integração com LLMs (OpenAI, Gemini, Deepseek).
"""
import os

class LanguageModelService:
    """Interface para provedores de LLM."""
    def __init__(self, provider: str):
        self.provider = provider
        self.api_key = os.getenv("LLM_API_KEY")
        # Inicialização específica do provider

    def chat(self, messages, **kwargs):
        """Envia mensagens para o LLM e retorna a resposta."""
        raise NotImplementedError

class OpenAIService(LanguageModelService):
    def __init__(self):
        super().__init__('OPENAI')
        # TODO: inicializar cliente OpenAI usando self.api_key
    def chat(self, messages, **kwargs):
        # TODO: implementar chamada OpenAI
        pass

class GeminiService(LanguageModelService):
    def __init__(self):
        super().__init__('GOOGLE')
        # TODO: inicializar cliente Gemini usando self.api_key
    def chat(self, messages, **kwargs):
        # TODO: implementar chamada Gemini
        pass

class DeepseekService(LanguageModelService):
    def __init__(self):
        super().__init__('DEEPSEEK')
        # TODO: inicializar cliente Deepseek usando self.api_key
    def chat(self, messages, **kwargs):
        # TODO: implementar chamada Deepseek
        pass

def get_llm_service():
    provider = os.getenv('LLM_PROVIDER', 'OPENAI').upper()
    if provider == 'OPENAI':
        return OpenAIService()
    elif provider == 'GOOGLE':
        return GeminiService()
    elif provider == 'DEEPSEEK':
        return DeepseekService()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}") 