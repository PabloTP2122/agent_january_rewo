"use client";

export interface DietInfoHeaderProps {
  dietType: string;
  totalCalories: number;
}

export function DietInfoHeader({ dietType, totalCalories }: DietInfoHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <h2 className="w-40 text-lg font-semibold text-gray-800">Tipo de dieta</h2>
        <div className="bg-green-500 text-white rounded-lg px-4 py-2 text-center font-bold min-w-[150px]">
          <span>{dietType}</span>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <h2 className="w-40 text-lg font-semibold text-gray-800">Calorías</h2>
        <div className="bg-purple-600 text-white rounded-lg px-4 py-2 text-center font-bold min-w-[150px]">
          <span>{totalCalories} kcal</span>
        </div>
      </div>
    </div>
  );
}
