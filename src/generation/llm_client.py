"""LLM API client for DeepSeek/Groq."""
import httpx
from core.config import config

class LLMClient:
    """Client for cloud LLM API."""

    def __init__(self):
        self.provider = config.online.provider
        self.model = config.online.model
        self.temperature = config.online.temperature
        self.max_tokens = config.online.max_tokens

    def generate(self, context: str, query:str, system_prompt) -> str:
        """
        Send request to LLM API.

        Args:
            - context: formatted chunks text
            - query: user query
            - system_prompt: system prompt

        Returns:
            - generated response
        """
            
        from generation.prompt import USER_PROMPT_TEMPLATE

        user_prompt = USER_PROMPT_TEMPLATE.format(context=context, query=query)

        if self.provider == "deepseek":
            return self._call_deepseek(system_prompt, user_prompt)
        
        elif self.provider == "groq":
            return self._call_groq(system_prompt, user_prompt)
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        

    def _call_deepseek(self, system: str, user: str) -> str:
        """Call DeepSeek API."""

        api_key = config.env.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Set DEEPSEEK_API_KEY in .env")

        response = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=60,
        )
        
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def _call_groq(self, system: str, user: str) -> str:
        """Call Groq API."""
        api_key = config.env.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Set GROQ_API_KEY in .env")

        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=60,
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]