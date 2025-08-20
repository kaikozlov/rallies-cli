# OpenRouter Usage Example

To use rallies-cli with OpenRouter instead of OpenAI, you can initialize the LLM class with the provider parameter:

```python
from rallies.llm import LLM
import os

# Set your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "your-openrouter-api-key"

# Initialize LLM with OpenRouter provider
llm = LLM(provider="openrouter")

# Use OpenRouter models
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
]

# Non-streaming response
response = llm.prompt(messages, model="openai/gpt-4o")
print(response)

# Streaming response
for chunk in llm.prompt_stream(messages, model="openai/gpt-4o"):
    print(chunk, end="", flush=True)
```

For a list of available models on OpenRouter, please visit the [OpenRouter documentation](https://openrouter.ai/docs#models).