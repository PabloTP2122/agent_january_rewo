import os

from copilotkit.langgraph import RunnableConfig
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from agent.state import State

load_dotenv()
model_google = "google_genai:gemini-2.5-flash"
open_ai_model = "openai:gpt-4o"
# api_key = os.getenv("GOOGLE_API_KEY")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    # raise ValueError("¡Falta GOOGLE_API_KEY en el .env!")
    raise ValueError("¡Falta OPENAI_API_KEY en el .env!")
try:
    llm = init_chat_model(model=open_ai_model, temperature=0)
except Exception as e:
    raise e


# TODO: agregar una structured output para representarlo en la UI.
def simple_node_agentui(state: State, config: RunnableConfig) -> dict:
    """Un nodo simple que solo responde al último mensaje."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
