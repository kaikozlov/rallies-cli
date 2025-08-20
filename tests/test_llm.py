import pytest
import os
from unittest.mock import Mock, patch
from src.rallies.llm import LLM

# Test for OpenAI provider
def test_llm_openai_initialization():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
        llm = LLM(provider="openai")
        assert llm.provider == "openai"
        assert llm.client.api_key == "test-openai-key"

# Test for OpenRouter provider
def test_llm_openrouter_initialization():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"}):
        llm = LLM(provider="openrouter")
        assert llm.provider == "openrouter"
        assert llm.client.api_key == "test-openrouter-key"
        assert str(llm.client.base_url) == "https://openrouter.ai/api/v1/"

# Test for unsupported provider
def test_llm_unsupported_provider():
    with pytest.raises(ValueError) as excinfo:
        LLM(provider="unsupported")
    assert "Unsupported provider" in str(excinfo.value)

# Test default provider (openai)
def test_llm_default_provider():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
        llm = LLM()  # Should default to openai
        assert llm.provider == "openai"
        assert llm.client.api_key == "test-openai-key"