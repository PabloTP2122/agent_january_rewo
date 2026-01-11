🎯 Objetivo
Este documento establece los estándares no negociables para la creación de herramientas (tools) en agentes de LangGraph. El propósito es garantizar que el LLM funcione como el Cerebro (razonamiento) y la herramienta como las Manos (ejecución).

🏗️ 1. Filosofía de Diseño: "Cerebro vs. Manos"
El LLM es el Cerebro: Debe decidir qué hacer y por qué.

La Herramienta son las Manos: Debe ejecutar la acción de forma determinista y reportar resultados.

Abstracción de Tarea: Define herramientas basadas en tareas de usuario, no en puntos finales de una API.

Mal: call_calendar_api_v3(headers, flags, ...)

Bien: agendar_reunion(fecha, participantes)

📝 2. Documentación y Semántica
La documentación es la interfaz de comunicación con el modelo.

Nombre de la Herramienta: Debe ser un verbo de acción claro y conciso.

Descripción de Acción: Describe qué hace la herramienta, nunca detalles de implementación interna.

Instrucciones de Uso: Indica al modelo la tarea que debe realizar (ej. "Usa esta herramienta para reportar un bug") en lugar de cómo llamarla técnicamente.

🧩 3. Granularidad y Encapsulamiento
Responsabilidad Única: Cada herramienta debe realizar una sola cosa. Si una herramienta se vuelve compleja, divídela en varias más pequeñas.

Ocultar Complejidad Legacy: No expongas parámetros técnicos innecesarios (IDs internos, banderas de sistema, tokens). Encapsúlalos dentro de la lógica de la herramienta.

Publicar Tareas, no Wrappers: Evita crear envoltorios directos de APIs empresariales con docenas de parámetros.

✅ 4. Validación y Schemas (Strict Typing)
Schema Obligatorio: Todas las herramientas deben usar esquemas de validación (Pydantic en Python / Zod en TS).

Doble Función:

Documentación: Sirve para que el LLM entienda los tipos de datos requeridos.

Runtime Check: Valida la entrada antes de la ejecución para evitar fallos catastróficos.

⚡ 5. Diseño de la Respuesta (Output)
El diseño de la respuesta afecta directamente la latencia y el razonamiento del modelo.

Respuesta Concisa: Evita retornar JSONs masivos o datos en bruto.

Resúmenes y Referencias: Prefiere retornar un resumen ejecutivo o una URI/Referencia a un objeto almacenado externamente (ej. Google ADK Artifacts).

Token Efficiency: Menos datos irrelevantes = Menos costo, menos latencia y mejor razonamiento del LLM.

⚠️ 6. Mensajes de Error Instructivos
Los errores no deben ser el fin del flujo, sino una guía para el Cerebro.

No usar códigos genéricos: Evita "Error 500".

Errores Accionables: Indica qué salió mal y cómo puede el LLM intentar recuperarse.

Ejemplo: "Límite de API alcanzado. Por favor, espera 15 segundos antes de reintentar esta acción."

🚦 Checklist de Verificación para Cursor.ai
Al generar o revisar una herramienta, el LLM debe validar:

[ ] ¿La descripción se enfoca en la tarea y no en el código?

[ ] ¿Tiene un schema de validación riguroso para los argumentos?

[ ] ¿La herramienta hace una sola cosa?

[ ] ¿La respuesta es corta y libre de datos basura?

[ ] ¿Los mensajes de error son instructivos para el modelo?
