"""Nutrition Agent: Plan-and-Execute architecture with HITL support.

This agent generates personalized nutrition plans using:
- Parallel batch meal generation (~60% latency reduction)
- Single HITL review point for complete plan
- Deterministic calculations (TDEE, macros)
- RAG-based calorie validation

Usage:
    from src.nutrition_agent import graph, make_graph

    # Default graph (no checkpointer, for langgraph dev)
    result = await graph.ainvoke({"messages": [...]})

    # Custom checkpointer (for FastAPI modes)
    custom_graph = make_graph(checkpointer=my_checkpointer)
"""

from src.nutrition_agent.graph import graph, make_graph

__all__ = ["graph", "make_graph"]
