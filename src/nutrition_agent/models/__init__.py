"""Models for structured output/input.

user_profile: input user data.
nutritional_targets: resulting TDEE and macro computations.
diet_plan: final daily recipies structure.
"""

from src.nutrition_agent.models.user_profile import UserProfile

__all__ = ["UserProfile"]
