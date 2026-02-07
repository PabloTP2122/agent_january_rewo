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
    <div className="mt-6">
      <h2 className="text-lg font-semibold mb-2 text-gray-800">Macronutrientes:</h2>
      <div className="overflow-hidden rounded-lg border border-gray-300">
        <table className="w-full text-left">
          <tbody>
            <tr className="bg-green-500 text-white">
              <td className="p-3 font-medium">Total</td>
              <td className="p-3">(100%) ({totalCalories} kcal)</td>
            </tr>
            <tr className="border-t border-gray-300 text-gray-900">
              <td className="p-3 font-medium">Proteínas</td>
              <td className="p-3">
                ({macros.protein_percentage}%) ({Math.round(proteinCals)} kcal) ({macros.protein_grams}g)
              </td>
            </tr>
            <tr className="border-t border-gray-300 bg-gray-50 text-gray-900">
              <td className="p-3 font-medium">Carbohidratos</td>
              <td className="p-3">
                ({macros.carbs_percentage}%) ({Math.round(carbsCals)} kcal) ({macros.carbs_grams}g)
              </td>
            </tr>
            <tr className="border-t border-gray-300 text-gray-900">
              <td className="p-3 font-medium">Grasas</td>
              <td className="p-3">
                ({macros.fat_percentage}%) ({Math.round(fatCals)} kcal) ({macros.fat_grams}g)
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
