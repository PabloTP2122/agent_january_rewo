# Plan de Refactorización: Worker Tools

## Resumen Ejecutivo

Análisis del archivo `src/rewoo_agent/nodes/worker/tools.py` evaluando:
1. Cumplimiento del principio DRY (Don't Repeat Yourself)
2. Adherencia a las mejores prácticas de `.cursor/commands/checktool.md`

---

## 1. Violaciones DRY Identificadas

### 1.1 Configuración de Pydantic Inconsistente

**Problema:** Solo 2 de 7 schemas tienen `model_config = {"extra": "forbid"}`.

| Schema | Tiene `extra: forbid` |
|--------|----------------------|
| `SumTotalInput` | ✅ Sí (línea 57) |
| `VerifyIngredientsInput` | ✅ Sí (línea 71) |
| `NutritionalInput` | ❌ No |
| `MealDistInput` | ❌ No |
| `ConsolidateInput` | ❌ No |
| `IngredientInput` | ❌ No |
| `RecipeAnalysisInput` | ❌ No |

**Solución:** Crear clase base con configuración común.

```python
class StrictBaseModel(BaseModel):
    """Base para todos los schemas de input de tools."""
    model_config = {"extra": "forbid"}
```

### 1.2 Clase `_NutriFacts` Encapsulada

**Problema:** Definida dentro del método `get_extractor_chain()` (líneas 479-486). No es reutilizable ni testeable.

**Ubicación actual:**
```python
# Línea 479-486 dentro de ResourceLoader.get_extractor_chain()
class _NutriFacts(BaseModel):
    food_name: str
    calories_100g: float
    notes: str
```

**Solución:** Mover a nivel de módulo como `NutriFacts`.

### 1.3 Inconsistencia en Tipos de Ingredientes

**Problema:** Dos formas diferentes de representar ingredientes.

| Schema | Tipo | Ejemplo |
|--------|------|---------|
| `ConsolidateInput` | `list[str]` | `["200g Pechuga", "100g Arroz"]` |
| `RecipeAnalysisInput` | `list[IngredientInput]` | Objetos estructurados |

**Impacto:** El LLM debe entender dos formatos distintos para conceptos similares.

---

## 2. Evaluación contra Checklist (checktool.md)

### 2.1 ✅ Descripción enfocada en tarea

Todas las herramientas describen **qué hacen**, no **cómo lo hacen**:

- `generate_nutritional_plan`: "Calcula las necesidades calóricas diarias..."
- `sum_total_kcal`: "Suma una lista de calorías..."
- `calculate_recipe_nutrition`: "Consulta la base de conocimientos (RAG)..."

**Veredicto:** CUMPLE

### 2.2 ⚠️ Schema de validación riguroso

**Aspectos positivos:**
- Uso de `Field()` con constraints (`ge`, `le`, `gt`, `lt`, `min_length`)
- Enums para valores discretos (`ActivityLevel`, `Objective`, `DietType`)

**Aspectos a mejorar:**
- Inconsistencia en `extra: forbid`
- Falta de validadores personalizados para casos edge

**Veredicto:** PARCIALMENTE CUMPLE

### 2.3 ✅ Responsabilidad única

Cada herramienta hace exactamente una cosa:

| Tool | Responsabilidad |
|------|-----------------|
| `generate_nutritional_plan` | Calcular TDEE y macros |
| `sum_total_kcal` | Sumar calorías |
| `sum_ingredients_kcal` | Verificar sumas |
| `get_meal_distribution` | Distribuir calorías por comida |
| `consolidate_shopping_list` | Consolidar lista de compras |
| `calculate_recipe_nutrition` | Buscar info nutricional via RAG |

**Veredicto:** CUMPLE

### 2.4 ⚠️ Respuesta concisa

**Problema:** Prefijos verbosos en respuestas:

```python
# Actual (línea 190)
return f"TOTAL_CALCULADO: {round(total, 2)} kcal"

# Actual (línea 165)
return f"PLAN_GENERADO | TDEE: {int(tdee)}kcal | TARGET: {target_calories}kcal\n..."
```

**Impacto:** Tokens innecesarios que el LLM debe procesar.

**Solución sugerida:** Retornar datos estructurados o strings más limpios:

```python
# Propuesta
return f"{round(total, 2)} kcal"
```

**Veredicto:** PARCIALMENTE CUMPLE

### 2.5 ✅ Mensajes de error instructivos

Excelente implementación de errores accionables:

```python
# Línea 216-220
return (
    f"CORRECCIÓN REQUERIDA: La suma matemática real es {real_total} kcal "
    f"(Diferencia detectada: {diff} kcal). "
    f"STOP: No intentes recalcular. Actualiza tu respuesta final usando {real_total} kcal."
)
```

**Veredicto:** CUMPLE

---

## 3. Problemas Adicionales Detectados

### 3.1 Inconsistencia de Idioma

Mezcla de español e inglés en el código:

| Español | Inglés |
|---------|--------|
| `nombre`, `peso_gramos` | `food_name`, `calories_100g` |
| `"PLAN_GENERADO"` | `"ERROR"`, `"MISSING"` |
| `ingredientes` | `ingredients` |

**Recomendación:** Estandarizar en un solo idioma (preferiblemente inglés para el código, español para mensajes al usuario).

### 3.2 Singleton `ResourceLoader`

**Problema:** Patrón singleton dificulta testing y manejo de errores.

**Ubicación:** Líneas 421-494

**Recomendación:** Considerar inyección de dependencias o factory pattern.

---

## 4. Plan de Implementación

### Fase 1: Consolidación DRY (Prioridad Alta)

#### Tarea 1.1: Crear `StrictBaseModel`
```
Archivo: src/rewoo_agent/nodes/worker/tools.py
Línea: ~17 (después de imports)
Acción: Agregar clase base
Esfuerzo: Bajo
```

#### Tarea 1.2: Migrar schemas existentes
```
Archivos afectados: tools.py
Schemas a modificar: NutritionalInput, MealDistInput, ConsolidateInput,
                     IngredientInput, RecipeAnalysisInput
Acción: Heredar de StrictBaseModel
Esfuerzo: Bajo
```

#### Tarea 1.3: Extraer `_NutriFacts`
```
Archivo: src/rewoo_agent/nodes/worker/tools.py
Línea actual: 479-486 (dentro de método)
Línea destino: ~405 (nivel de módulo)
Acción: Mover clase y renombrar a NutriFacts
Esfuerzo: Bajo
```

### Fase 2: Limpieza de Respuestas (Prioridad Media)

#### Tarea 2.1: Simplificar outputs de `sum_total_kcal`
```
Archivo: tools.py
Línea: 190
Cambio: Eliminar prefijo "TOTAL_CALCULADO:"
```

#### Tarea 2.2: Estructurar output de `generate_nutritional_plan`
```
Archivo: tools.py
Líneas: 164-172
Cambio: Considerar retornar dict en lugar de string formateado
```

### Fase 3: Estandarización de Idioma (Prioridad Baja)

#### Tarea 3.1: Unificar nombres de campos
```
Decisión requerida: ¿Español o inglés para campos internos?
Campos a revisar: nombre, peso_gramos, ingredientes
```

---

## 5. Matriz de Cumplimiento Final

| Criterio | Estado | Acción Requerida |
|----------|--------|------------------|
| DRY - Configuración Pydantic | ⚠️ | Fase 1.1, 1.2 |
| DRY - Clase NutriFacts | ⚠️ | Fase 1.3 |
| Descripción en tarea | ✅ | Ninguna |
| Schema riguroso | ⚠️ | Fase 1.1, 1.2 |
| Responsabilidad única | ✅ | Ninguna |
| Respuesta concisa | ⚠️ | Fase 2.1, 2.2 |
| Errores instructivos | ✅ | Ninguna |

---

## 6. Código de Referencia

### StrictBaseModel propuesto

```python
from pydantic import BaseModel

class StrictBaseModel(BaseModel):
    """
    Clase base para todos los schemas de input de herramientas.

    Configuración:
    - extra="forbid": Rechaza campos no declarados (anti-alucinación)
    """
    model_config = {"extra": "forbid"}
```

### Ejemplo de migración

```python
# Antes
class MealDistInput(BaseModel):
    total_calories: float = Field(...)
    number_of_meals: int = Field(...)

# Después
class MealDistInput(StrictBaseModel):
    total_calories: float = Field(...)
    number_of_meals: int = Field(...)
```

---

**Fecha de análisis:** 2026-01-15
**Archivos analizados:**
- `src/rewoo_agent/nodes/worker/tools.py`
- `.cursor/commands/checktool.md`
