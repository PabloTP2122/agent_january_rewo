# Árbol de Decisión: Arquitectura del Agente de Nutrición

```
                         ┌──────────────────────────────────┐
                         │  Agente de Planificación         │
                         │  Nutricional                     │
                         │                                  │
                         │  Requerimientos:                 │
                         │  • Recopilación de datos usuario │
                         │  • Fine-tuning support           │
                         │  • Eficiencia tokens             │
                         │  • Precisión alta                │
                         │  • Output estructurado           │
                         └──────────────┬───────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────────┐
                         │  ¿Necesitas recopilar datos      │
                         │  del usuario conversacionalmente?│
                         └──────────────┬───────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ SÍ                                    │ NO (datos pre-provistos)
                    ▼                                       ▼
        ┌──────────────────────────┐          ┌──────────────────────────┐
        │  ReWOO ❌                │          │  ReWOO ✅                │
        │  No soporta flujo        │          │  Viable si datos         │
        │  conversacional          │          │  completos desde inicio  │
        └──────────────────────────┘          └──────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────────────────────────┐
        │  ¿Necesitas manejo robusto de errores        │
        │  (ej: ingrediente no encontrado en RAG)?     │
        └──────────────┬───────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │ SÍ                    │ NO
           ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│  ReWOO ❌           │   │  ReWOO ⚠️           │
│  No puede           │   │  Posible pero       │
│  replanificar       │   │  frágil             │
└─────────────────────┘   └─────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  ¿Qué tan crítica es la token efficiency?   │
└──────────────┬───────────────────────────────┘
               │
   ┌───────────┴─────────────┐
   │ MUY CRÍTICA              │ IMPORTANTE (pero no crítica)
   │ (<2,500 tokens target)   │ (<3,500 tokens aceptable)
   ▼                          ▼
┌──────────────────┐   ┌──────────────────────┐
│  Plan-and-       │   │  ReAct              │
│  Execute         │   │                      │
│                  │   │  ✅ Más simple      │
│  ✅ ~2,800 tok   │   │  ✅ Adaptable       │
│  ✅ Validación   │   │  ⚠️ ~3,500 tokens   │
│  ✅ Fine-tuning  │   │  ✅ Fine-tuning     │
│                  │   │  ✅ Debugging fácil │
└──────────────────┘   └──────────────────────┘
        │                          │
        └──────────┬───────────────┘
                   ▼
       ┌─────────────────────────────┐
       │  DECISIÓN FINAL             │
       │                             │
       │  RECOMENDADO:               │
       │  Plan-and-Execute           │
       │                             │
       │  ALTERNATIVA RÁPIDA:        │
       │  ReAct Optimizado           │
       │                             │
       │  NO RECOMENDADO:            │
       │  ReWOO (arquitectura actual)│
       └─────────────────────────────┘
```

## Matriz de Decisión Rápida

| Criterio | ReWOO | ReAct | Plan-and-Execute |
|----------|-------|-------|------------------|
| Recopilación datos conversacional | ❌ | ✅✅✅ | ✅✅✅ |
| Manejo de errores RAG | ❌ | ✅✅✅ | ✅✅✅ |
| Token efficiency | ✅✅✅✅✅ | ✅✅ | ✅✅✅✅ |
| Fine-tuning viability | ✅✅ | ✅✅✅✅ | ✅✅✅✅✅ |
| Precisión validación | ✅✅ | ✅✅✅ | ✅✅✅✅✅ |
| Simplicidad implementación | ✅✅✅ | ✅✅✅✅✅ | ✅✅ |
| Debugging | ✅✅ | ✅✅✅✅ | ✅✅✅✅✅ |
| **TOTAL (puntos)** | **17/35** | **27/35** | **32/35** |
| **RECOMENDACIÓN** | ❌ NO | ⚠️ OK (MVP) | ✅ SÍ |

## Timeline de Implementación

### Opción A: Plan-and-Execute (4 semanas)
```
Semana 1: Data Collector Node
  ├── Día 1-2: Diseño + Spec
  ├── Día 3-4: Implementación
  └── Día 5: Tests unitarios

Semana 2: High-Level Planner + Executor
  ├── Día 1-2: Refactor estado
  ├── Día 3-4: Planner node
  └── Día 5: Executor node

Semana 3: Reviewer + Replanner
  ├── Día 1-2: Reviewer con validaciones matemáticas
  ├── Día 3-4: Replanner con estrategias de fallback
  └── Día 5: Integración completa

Semana 4: Testing + Evaluación
  ├── Día 1-2: Tests E2E
  ├── Día 3: RAGAS evaluation
  ├── Día 4: Optimización de prompts
  └── Día 5: Documentación
```

### Opción B: ReAct Optimizado (1.5 semanas)
```
Semana 1:
  ├── Día 1-2: Data Collector + ask_user tool
  ├── Día 3-4: ReAct loop con batching
  └── Día 5: Optimizaciones (límites, caching)

Semana 2 (parcial):
  ├── Día 1: Tests unitarios
  ├── Día 2: Tests de integración
  └── Día 3: Comparación métricas vs ReWOO
```

## Costos Estimados (GPT-4o)

### Por conversación completa:

| Arquitectura | Input Tokens | Output Tokens | Costo (USD) |
|--------------|--------------|---------------|-------------|
| ReWOO | ~2,000 | ~500 | $0.0125 |
| ReAct | ~2,800 | ~700 | $0.0175 |
| Plan-and-Execute | ~2,200 | ~600 | $0.0140 |

**Diferencia mensual** (1,000 usuarios):
- ReWOO → Plan-and-Execute: +$1.50/mes
- ReWOO → ReAct: +$5.00/mes

**Conclusión**: La diferencia de costo es marginal comparada con la mejora en calidad.

## Estrategia de Fine-Tuning

### Plan-and-Execute (RECOMENDADO):
```
Dataset Structure:
├── planner_dataset.jsonl (200+ ejemplos)
│   ├── {user_query, user_profile} → high_level_plan
│   └── Fine-tune: gpt-4o-mini-2024-07-18
├── executor_dataset.jsonl (500+ ejemplos)
│   ├── {step, context} → {tool, args}
│   └── Fine-tune: gpt-4o-mini-2024-07-18
└── reviewer_dataset.jsonl (300+ ejemplos)
    ├── {step_result, expected} → {valid, reason}
    └── Fine-tune: gpt-4o-mini-2024-07-18 (opcional)

Costo estimado de fine-tuning:
  Planner: ~$10 (200 ejemplos × 1 epoch)
  Executor: ~$25 (500 ejemplos × 2 epochs)
  Total: ~$35 USD
```

### ReAct:
```
Dataset Structure:
└── react_dataset.jsonl (400+ ejemplos)
    ├── {conversation_history} → {thought, action}
    └── Fine-tune: gpt-4o-mini-2024-07-18

Costo estimado: ~$20 USD
```

## Recomendación Final

1. **Si tienes 4 semanas**: Implementa **Plan-and-Execute**
   - Mejor calidad
   - Mejor fine-tuning
   - Mejor debugging
   - Costo marginal aceptable

2. **Si necesitas MVP en 1.5 semanas**: Implementa **ReAct Optimizado**
   - Más simple
   - Calidad aceptable
   - Migración a Plan-and-Execute posterior es viable

3. **NO continúes con ReWOO**
   - No cumple requerimientos de recopilación de datos
   - Frágil ante errores
   - Dificulta fine-tuning
   - Ahorro de tokens no compensa deficiencias
