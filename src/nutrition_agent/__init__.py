"""Nutrition Agent: Plan-and-Execute architecture with HITL support.

This agent generates personalized nutrition plans using:
- Parallel batch meal generation (~60% latency reduction)
- Single HITL review point for complete plan
- Deterministic calculations (TDEE, macros)
- RAG-based calorie validation

Usage:
    from src.nutrition_agent import graph

    # Run the graph
    result = await graph.ainvoke({"messages": [...]})
"""

from src.nutrition_agent.graph import graph

__all__ = ["graph"]
