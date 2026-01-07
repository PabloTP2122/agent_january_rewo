from langgraph.graph import END, START, StateGraph

from agent.node import simple_node_agentui
from agent.state import State

workflow = StateGraph(State)
workflow.add_node("agent", simple_node_agentui)

workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

graph = workflow.compile()
