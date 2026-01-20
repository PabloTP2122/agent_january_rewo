"""Quick /smoke test for food facts RAG tool."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.rewoo_agent.nodes.worker.tools import calculate_recipe_nutrition  # noqa: E402

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno (Simulación del orquestador)
load_dotenv()

# Datos de prueba: Un ingrediente común y uno que quizás no exista
test_input = {
    "ingredientes": [
        {"nombre": "Plátano", "peso_gramos": 150},
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

    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")


if __name__ == "__main__":
    # Punto de entrada estándar para scripts async
    asyncio.run(run_test())
