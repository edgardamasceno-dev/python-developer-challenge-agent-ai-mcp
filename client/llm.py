"""
Abstração para integração com LLMs (OpenAI, Gemini, Deepseek).
"""
import os
import openai

class LanguageModelService:
    """Interface para provedores de LLM."""
    def __init__(self, provider: str):
        self.provider = provider
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
        # Inicialização específica do provider

    def chat(self, messages, **kwargs):
        """Envia mensagens para o LLM e retorna a resposta."""
        raise NotImplementedError

class OpenAIService(LanguageModelService):
    def __init__(self):
        super().__init__('OPENAI')
        self.client = openai.OpenAI(api_key=self.api_key)
    def chat(self, messages, **kwargs):
        # Converte mensagens para o formato OpenAI
        openai_msgs = []
        for m in messages:
            role = m.get("role")
            if role == "tool":
                openai_msgs.append({"role": "system", "content": f"Tool {m.get('name')}: {m.get('content')}"})
            else:
                openai_msgs.append({"role": role, "content": m.get("content")})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_msgs,
                temperature=0.2,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[LLM Error: {e}]"

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