"use client";

export interface DietInfoHeaderProps {
  dietType: string;
  totalCalories: number;
}

export function DietInfoHeader({ dietType, totalCalories }: DietInfoHeaderProps) {
  return (
    <div
      className="space-y-4 animate-fade-in"
      role="region"
      aria-label="Resumen del plan nutricional"
    >
      <dl className="space-y-4">
        <div className="flex items-center space-x-4">
          <dt className="w-40 text-lg font-semibold text-gray-800">
            Tipo de dieta
          </dt>
          <dd
            className="bg-green-500 text-white rounded-lg px-4 py-2 text-center font-bold min-w-[150px] hover:bg-green-600 transition-colors"
            aria-label={`Tipo de dieta: ${dietType}`}
          >
            {dietType}
          </dd>
        </div>
        <div className="flex items-center space-x-4">
          <dt className="w-40 text-lg font-semibold text-gray-800">
            Calorías
          </dt>
          <dd
            className="bg-purple-600 text-white rounded-lg px-4 py-2 text-center font-bold min-w-[150px] hover:bg-purple-700 transition-colors"
            aria-label={`Calorías diarias objetivo: ${totalCalories} kilocalorías`}
          >
            {totalCalories} kcal
          </dd>
        </div>
      </dl>
    </div>
  );
}
