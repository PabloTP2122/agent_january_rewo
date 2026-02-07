"use client";

import type { DebugInfo } from "@/lib/types";
import { Badge } from "@/components/ui";

export interface CanvasDebugPanelProps {
  debug: DebugInfo;
}

const phaseColors: Record<string, "success" | "warning" | "error" | "info" | "default"> = {
  idle: "default",
  data_collection: "info",
  calculation: "info",
  recipe_generation: "info",
  meal_review: "warning",
  validation: "info",
  complete: "success",
  error: "error",
};

const phaseLabels: Record<string, string> = {
  idle: "Inactivo",
  data_collection: "Recopilando datos",
  calculation: "Calculando",
  recipe_generation: "Generando recetas",
  meal_review: "Revisión HITL",
  validation: "Validando",
  complete: "Completado",
  error: "Error",
};

export function CanvasDebugPanel({ debug }: CanvasDebugPanelProps) {
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  return (
    <div className="bg-gray-100 rounded-lg p-3 text-sm space-y-2 border border-gray-200">
      <div className="flex items-center justify-between">
        <span className="text-gray-600">Fase:</span>
        <Badge variant={phaseColors[debug.phase] || "default"} size="sm">
          {phaseLabels[debug.phase] || debug.phase}
        </Badge>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-gray-600">Tiempo:</span>
        <span className="font-mono text-gray-800">{formatTime(debug.elapsed_seconds)}</span>
      </div>

      {debug.tools_invoked.length > 0 && (
        <div>
          <span className="text-gray-600">Herramientas:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {debug.tools_invoked.map((tool, index) => (
              <Badge key={index} variant="default" size="sm">
                {tool}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {debug.last_error && (
        <div className="text-red-600 text-xs mt-2 p-2 bg-red-50 rounded">
          {debug.last_error}
        </div>
      )}
    </div>
  );
}
