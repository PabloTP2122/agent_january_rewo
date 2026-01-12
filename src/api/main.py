from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import graph
from database.session import CheckpointerDep, lifespan

load_dotenv()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAGUIAgent(
            name="simple_agent",
            description="Agente UI simple",
            graph=graph,
        )
    ]
)

add_fastapi_endpoint(app, sdk, "/copilotkit")


@app.get("/health")  # type: ignore [misc]
def health() -> dict:
    """Health check."""
    return {"status": "ok"}


class Message(BaseModel):
    message: str


@app.post("/chat_memory/{chat_id}")  # type: ignore [misc]
async def chat_simple_memory(
    chat_id: str, item: Message, checkpointer: CheckpointerDep
) -> str:
    return "Not implemented endpoint"
