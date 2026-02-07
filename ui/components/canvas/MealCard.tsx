"use client";

import type { Meal } from "@/lib/types";

export interface MealCardProps {
  meal: Meal;
}

export function MealCard({ meal }: MealCardProps) {
  return (
    <section className="bg-white rounded-2xl p-6 pt-12 mt-16 relative shadow-md">
      <div className="absolute -top-6 -left-6 bg-green-500 text-white font-bold text-xl px-6 py-2 rounded-lg shadow-lg">
        {meal.meal_time}
      </div>

      <div className="mb-6 pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800">{meal.title}</h2>
        <p className="font-semibold text-gray-600">
          {meal.description} ({meal.total_calories} kcal)
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <h3 className="text-xl font-semibold mb-2 text-green-600">Ingredientes:</h3>
          <ul className="list-disc list-inside space-y-1 text-gray-700 marker:text-green-500">
            {meal.ingredients.map((ingredient, index) => (
              <li key={index}>{ingredient}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-xl font-semibold mb-2 text-green-600">Alternativa:</h3>
          <p className="text-gray-700">{meal.alternative ?? "N/A"}</p>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-xl font-semibold mb-2 text-green-600">Preparación:</h3>
        <ol className="list-decimal list-inside space-y-2 text-gray-700">
          {meal.preparation.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
      </div>
    </section>
  );
}
