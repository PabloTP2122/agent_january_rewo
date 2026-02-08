from typing import Any

# =============================================================================
# calculate_recipe_nutrition tests (async - requires API keys)
#    These are smoke tests that require PINECONE_API_KEY and OPENAI_API_KEY
#    Skipped if environment variables are not set
# =============================================================================


def test_calculate_recipe_nutrition_missing_env() -> None:
    """Test that missing env vars return appropriate error."""
    import asyncio
    import os

    from src.nutrition_agent.nodes.recipe_generation.tool import (
        ResourceLoader,
        calculate_recipe_nutrition,
    )

    # Reset singleton to force re-initialization
    ResourceLoader._retriever = None
    ResourceLoader._extractor_llm = None

    # Temporarily remove env vars if they exist
    original_pinecone = os.environ.pop("PINECONE_API_KEY", None)
    original_openai = os.environ.pop("OPENAI_API_KEY", None)

    async def _run_test() -> dict[str, Any]:
        result = await calculate_recipe_nutrition.ainvoke(
            {"ingredientes": [{"nombre": "Pollo", "peso_gramos": 100}]}
        )
        return result  # type: ignore[no-any-return]

    try:
        result = asyncio.run(_run_test())

        # Should return error dict when env vars missing
        assert isinstance(result, dict)
        assert "system_error" in result or "error" in str(result).lower()
    finally:
        # Restore env vars
        if original_pinecone:
            os.environ["PINECONE_API_KEY"] = original_pinecone
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai
        # Reset singleton again
        ResourceLoader._retriever = None
        ResourceLoader._extractor_llm = None
