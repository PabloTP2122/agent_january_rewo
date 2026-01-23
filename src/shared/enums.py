# File: src/shared/enums.py
"""Standardized enums for nutrition agent to prevent LLM hallucinations."""

from enum import StrEnum


class ActivityLevel(StrEnum):
    """Niveles de actividad estandarizados para evitar ambigüedad."""

    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class Objective(StrEnum):
    """Objetivos claros para guiar el cálculo calórico."""

    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


class DietType(StrEnum):
    """Tipos de dieta soportados."""

    NORMAL = "normal"
    KETO = "keto"


class MealTime(StrEnum):
    """Tiempos de comida válidos."""

    DESAYUNO = "Desayuno"
    ALMUERZO = "Almuerzo"
    COMIDA = "Comida"
    CENA = "Cena"
    SNACK = "Snack"
