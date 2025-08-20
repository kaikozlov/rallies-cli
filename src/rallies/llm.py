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
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @retry_json_decode()
    def prompt(self, messages, model=None, requires_json=False, response_format=None):
        model_to_use = model or get_default_model()
        kwargs = {
            "model": model_to_use,
            "input": messages,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        response = self.client.responses.create(**kwargs)
        response_text = response.output_text
        if requires_json:
            response_text = json.loads(response_text)
        return response_text
    
    def prompt_stream(self, messages, model=None):
        model_to_use = model or get_default_model()
        response = self.client.responses.create(
            model=model_to_use,
            input=messages,
            stream=True
        )
        for event in response:
            # Listen for text delta events to get streaming content
            if event.type == "response.output_text.delta":
                yield event.delta