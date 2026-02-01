"""Quick /smoke test for food facts RAG tool."""

# Disable LangSmith before any LangChain imports to avoid connection timeouts
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

# Force LangSmith off after .env so .env
# cannot re-enable it (avoids api.smith.langchain.com timeout)
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
# Unset API key so LangChain never tries to connect to LangSmith in this process
os.environ.pop("LANGSMITH_API_KEY", None)

# Skip test when RAG dependencies are not configured (avoids hanging on Pinecone)
_required = ("PINECONE_API_KEY", "PINECONE_INDEX_NAME", "OPENAI_API_KEY")
_missing = [v for v in _required if not os.getenv(v)]
if _missing:
    print(
        f"Skipping: missing env vars {_missing}. "
        "Set them to run the RAG tool (e.g. in .env)."
    )
    sys.exit(0)

from src.nutrition_agent.nodes.recipe_generation.tool import (
    calculate_recipe_nutrition,
)  # noqa: E402

# Datos de prueba: Un ingrediente común y uno que quizás no exista
test_input = {
    "ingredientes": [
        {"nombre": "Platano maduro", "peso_gramos": 100},  # 137.0
        {"nombre": "Pechuga de Pollo", "peso_gramos": 200},  # 286.0
        {"nombre": "Arroz blanco cocido (sancochado)", "peso_gramos": 150},  # 159.0
        {"nombre": "Unicornio enlatado", "peso_gramos": 200},  # Caso borde
    ]
}


async def run_test() -> None:
    print("Ejecutando herramienta...")

    # Usamos .ainvoke para herramientas asíncronas
    try:
        resultado = await calculate_recipe_nutrition.ainvoke(test_input)

        print("\n RESULTADO OBTENIDO:")
        print("-" * 30)
        # Imprimimos bonito el diccionario
        import json

        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print("-" * 30)

    except ConnectionError as e:
        print(f"Conexión fallida (Pinecone/OpenAI): {e}")
        print("   Comprueba red y variables de entorno (.env).")
    except (OSError, TimeoutError) as e:
        print(f"Error de red o tiempo de espera: {e}")
    except Exception as e:
        print(f"Error en la ejecución: {e}")


if __name__ == "__main__":
    # Punto de entrada estándar para scripts async
    asyncio.run(run_test())
