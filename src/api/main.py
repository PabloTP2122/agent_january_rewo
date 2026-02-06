import uvicorn
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nutrition_agent import graph as nutrition_graph

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definición del SDK con Agentes AG-UI
""" sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAGUIAgent(
            name="simple_agent",
            description="Agente verificador de conexión",
            graph=simple_graph,
        ),
        LangGraphAGUIAgent(
            name="nutrition_agent",
            description="Agente de planificación nutricional personalizada",
            graph=nutrition_graph,
        ),
    ]
) """
add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="nutrition_agent",
        description="Agente de planificación nutricional personalizada",
        graph=nutrition_graph,
    ),
    path="/",
)


# uv run fastapi dev src/api/main.py --port 8123
# uv run uvicorn src.api.main:app --port 8123 --reload
def main() -> None:
    """Run the uvicorn server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # noqa: S104
        port="8123",
        reload=True,
    )


if __name__ == "__main__":
    main()
