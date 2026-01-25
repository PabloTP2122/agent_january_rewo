"""Data collection node for the nutrition agent.

This node extracts UserProfile data from the conversation using LLM
with structured output. It validates that all required fields are
present before allowing the workflow to proceed.
"""

from langchain_core.messages import SystemMessage

from src.nutrition_agent.models import UserProfile
from src.nutrition_agent.prompts import DATA_COLLECTION_PROMPT
from src.nutrition_agent.state import NutritionAgentState
from src.shared import get_llm

# Required fields that must be present for profile to be complete
REQUIRED_FIELDS = {"age", "gender", "weight", "height", "activity_level", "objective"}


async def data_collection(state: NutritionAgentState) -> dict:
    """Extract UserProfile from conversation using LLM structured output.

    This node:
    1. Checks if user_profile already exists and is complete
    2. If not, uses LLM to extract profile from messages
    3. Validates that all required fields are present
    4. Returns profile and any missing fields

    Args:
        state: Current agent state with messages and optional existing profile

    Returns:
        dict with:
        - user_profile: Extracted UserProfile (or None if incomplete)
        - missing_fields: List of fields still needed from user
    """
    # If profile already exists and is complete, skip extraction
    if state.get("user_profile") is not None and not state.get("missing_fields", []):
        return {}

    # Get messages from state
    messages = state.get("messages", [])
    if not messages:
        return {
            "user_profile": None,
            "missing_fields": list(REQUIRED_FIELDS),
        }

    # Use LLM with structured output to extract UserProfile
    # llm = get_llm("gemini-2.5-flash")
    llm = get_llm()
    structured_llm = llm.with_structured_output(UserProfile)

    try:
        # Invoke LLM with system prompt and conversation history
        profile = await structured_llm.ainvoke(
            [
                SystemMessage(content=DATA_COLLECTION_PROMPT),
                *messages,
            ]
        )

        # Profile successfully extracted - all fields present
        return {
            "user_profile": profile,
            "missing_fields": [],
        }

    except Exception:
        # LLM could not extract complete profile
        # Determine which fields are missing based on partial extraction
        # For now, return all required fields as missing
        return {
            "user_profile": None,
            "missing_fields": list(REQUIRED_FIELDS),
        }
