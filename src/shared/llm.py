# File: src/shared/llm.py
"""LLM factory with Helicone proxy for observability."""

import os

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def get_llm(model: str = "gpt-4o") -> BaseChatModel:
    """
    Returns LLM instance with Helicone proxy for OpenAI models.

    Args:
        model: Model name (gpt-4o, gpt-4o-mini, gemini-2.5-flash)

    Returns:
        Configured ChatOpenAI or ChatGoogleGenerativeAI instance

    Note:
        - OpenAI models: routed through Helicone proxy
        - Gemini models: direct connection (Helicone not supported)
    """
    helicone_api_key = os.getenv("HELICONE_API_KEY")

    if model.startswith("gemini"):
        # Gemini: direct connection (no Helicone support)
        return ChatGoogleGenerativeAI(model=model, temperature=0)

    # OpenAI: proxy via Helicone for observability
    return ChatOpenAI(
        model=model,
        base_url="https://oai.helicone.ai/v1",
        default_headers={"Helicone-Auth": f"Bearer {helicone_api_key}"},
    )
