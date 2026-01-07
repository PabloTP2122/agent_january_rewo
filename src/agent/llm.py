import os

from langchain_openai import OpenAI


def get_llm() -> OpenAI:
    """Configura el cliente OpenAI con el proxy de Helicone para observabilidad."""
    return OpenAI(
        model="gpt-4o",
        # El base_url de Helicone actúa como proxy
        base_url="https://oai.h7i.ai/v1",
        default_headers={
            "Helicone-Auth": f"Bearer {os.getenv('HELICONE_API_KEY')}",
            "Helicone-Cache-Enabled": "true",
        },
    )
