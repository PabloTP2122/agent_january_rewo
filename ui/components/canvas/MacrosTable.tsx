"use client";

import type { Macronutrients } from "@/lib/types";

export interface MacrosTableProps {
  macros: Macronutrients;
  totalCalories: number;
}

export function MacrosTable({ macros, totalCalories }: MacrosTableProps) {
  const proteinCals = macros.protein_grams * 4;
  const carbsCals = macros.carbs_grams * 4;
  const fatCals = macros.fat_grams * 9;

  return (
    <div className="mt-6 animate-fade-in">
      <h3 className="text-lg font-semibold mb-2 text-gray-800" id="macros-heading">
        Macronutrientes:
      </h3>
      <div className="overflow-hidden rounded-lg border border-gray-300">
        <table
          className="w-full text-left"
          aria-labelledby="macros-heading"
          role="table"
        >
          <caption className="sr-only">
            Distribución de macronutrientes del plan
          </caption>
          <thead className="sr-only">
            <tr>
              <th scope="col">Nutriente</th>
              <th scope="col">Valores</th>
            </tr>
          </thead>
          <tbody>
            <tr className="bg-green-500 text-white">
              <th scope="row" className="p-3 font-medium text-left">Total</th>
              <td className="p-3">(100%) ({totalCalories} kcal)</td>
            </tr>
            <tr className="border-t border-gray-300 text-gray-900 hover:bg-gray-50 transition-colors">
              <th scope="row" className="p-3 font-medium text-left">Proteínas</th>
              <td className="p-3">
                <span className="inline-flex items-center gap-2">
                  <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-sm">
                    {macros.protein_percentage}%
                  </span>
                  <span>{Math.round(proteinCals)} kcal</span>
                  <span className="font-semibold">{macros.protein_grams}g</span>
                </span>
              </td>
            </tr>
            <tr className="border-t border-gray-300 bg-gray-50 text-gray-900 hover:bg-gray-100 transition-colors">
              <th scope="row" className="p-3 font-medium text-left">Carbohidratos</th>
              <td className="p-3">
                <span className="inline-flex items-center gap-2">
                  <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-sm">
                    {macros.carbs_percentage}%
                  </span>
                  <span>{Math.round(carbsCals)} kcal</span>
                  <span className="font-semibold">{macros.carbs_grams}g</span>
                </span>
              </td>
            </tr>
            <tr className="border-t border-gray-300 text-gray-900 hover:bg-gray-50 transition-colors">
              <th scope="row" className="p-3 font-medium text-left">Grasas</th>
              <td className="p-3">
                <span className="inline-flex items-center gap-2">
                  <span className="bg-rose-100 text-rose-800 px-2 py-0.5 rounded text-sm">
                    {macros.fat_percentage}%
                  </span>
                  <span>{Math.round(fatCals)} kcal</span>
                  <span className="font-semibold">{macros.fat_grams}g</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
