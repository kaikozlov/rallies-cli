import os
import json
from openai import OpenAI
from functools import wraps

def retry_json_decode(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(self, messages, model="gpt-4.1", requires_json=False):
            if not requires_json:
                return func(self, messages, model, requires_json)
            
            for attempt in range(max_retries):
                try:
                    return func(self, messages, model, requires_json)
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
    def prompt(self, messages, model = "gpt-4.1", requires_json = False):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        response = response.choices[0].message.content
        if requires_json:
            response = json.loads(response)
        return response
    
    def prompt_stream(self, messages, model = "gpt-4.1"):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content