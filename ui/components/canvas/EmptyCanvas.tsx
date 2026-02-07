"use client";

import type { AgentPhase } from "@/lib/types";

export interface EmptyCanvasProps {
  phase?: AgentPhase;
}

const phaseMessages: Record<AgentPhase, { title: string; description: string; isLoading?: boolean }> = {
  idle: {
    title: "Bienvenido",
    description: "Inicia una conversación para crear tu plan nutricional personalizado.",
  },
  data_collection: {
    title: "Recopilando información",
    description: "Responde las preguntas del asistente para personalizar tu plan.",
  },
  calculation: {
    title: "Calculando objetivos",
    description: "Estamos calculando tu gasto energético y distribución de macros...",
    isLoading: true,
  },
  recipe_generation: {
    title: "Generando recetas",
    description: "Creando tus comidas personalizadas con los ingredientes ideales...",
    isLoading: true,
  },
  meal_review: {
    title: "Revisión de comidas",
    description: "Revisa las comidas generadas y aprueba o solicita cambios.",
  },
  validation: {
    title: "Validando plan",
    description: "Verificando que las calorías y macros cumplan con tus objetivos...",
    isLoading: true,
  },
  complete: {
    title: "Plan listo",
    description: "Tu plan nutricional ha sido generado exitosamente.",
  },
  error: {
    title: "Error",
    description: "Ha ocurrido un error. Por favor intenta de nuevo.",
  },
};

export function EmptyCanvas({ phase = "idle" }: EmptyCanvasProps) {
  const { title, description, isLoading } = phaseMessages[phase];

  return (
    <div
      className="flex flex-col items-center justify-center h-full text-center px-6"
      role="region"
      aria-label="Estado del plan nutricional"
    >
      {/* Status announcement for screen readers */}
      <div
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {title}: {description}
      </div>

      <div className="mb-6">
        <svg
          className="w-24 h-24 text-gray-300 mx-auto animate-fade-in"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>
      <h2 className="text-2xl font-semibold text-gray-700 mb-2 animate-fade-in">
        {title}
      </h2>
      <p className="text-gray-500 max-w-md animate-fade-in">
        {description}
      </p>

      {isLoading && (
        <div className="mt-6" role="status" aria-label="Cargando...">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto" />
          <span className="sr-only">Procesando, por favor espere...</span>
        </div>
      )}
    </div>
  );
}
