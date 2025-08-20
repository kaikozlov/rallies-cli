import os
import json
from openai import OpenAI
from functools import wraps

def get_default_model() -> str:
    """Resolve the default model dynamically from environment."""
    return os.getenv("RALLIES_MODEL", "gpt-4.1")

def retry_json_decode(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(self, messages, model=None, requires_json=False, response_format=None):
            if not requires_json:
                return func(self, messages, model, requires_json, response_format)
            for attempt in range(max_retries):
                try:
                    return func(self, messages, model, requires_json, response_format)
                except json.JSONDecodeError:
                    if attempt == max_retries - 1:
                        return []
                    continue
        return wrapper
    return decorator

class LLM:
    def __init__(self, provider="openai"):
        self.provider = provider.lower()
        
        if self.provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "openrouter":
            self.client = OpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @retry_json_decode()
    def prompt(self, messages, model=None, requires_json=False, response_format=None):
        model_to_use = model or get_default_model()
        kwargs = {
            "model": model_to_use,
            "messages": messages,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
            
        response = self.client.chat.completions.create(**kwargs)
        response_text = response.choices[0].message.content
        
        if requires_json:
            try:
                response_text = json.loads(response_text)
            except json.JSONDecodeError:
                if not hasattr(prompt, 'retry_count'):
                    prompt.retry_count = 0
                if prompt.retry_count < 3:
                    prompt.retry_count += 1
                    return self.prompt(messages, model, requires_json, response_format)
                else:
                    return []
        return response_text
    
    def prompt_stream(self, messages, model=None):
        model_to_use = model or get_default_model()
        response = self.client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content