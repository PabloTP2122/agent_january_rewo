"use client";

import type { Meal } from "@/lib/types";

export interface MealCardProps {
  meal: Meal;
  /** Animation delay index for staggered entrance */
  animationIndex?: number;
}

export function MealCard({ meal, animationIndex = 0 }: MealCardProps) {
  // Calculate stagger delay based on index (max 5 levels of stagger)
  const staggerClass = animationIndex > 0 && animationIndex <= 5
    ? `animate-stagger-${animationIndex}`
    : "";

  return (
    <section
      className={`
        bg-white rounded-2xl p-6 pt-12 mt-16 relative shadow-md
        animate-fade-slide-up ${staggerClass}
        hover:shadow-lg transition-shadow duration-300
      `}
      aria-label={`Comida: ${meal.title}`}
    >
      {/* Meal time badge with animation */}
      <div className="absolute -top-6 -left-6 bg-green-500 text-white font-bold text-xl px-6 py-2 rounded-lg shadow-lg transform hover:scale-105 transition-transform duration-200">
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
            {meal.ingredients.map((ing, index) => (
              <li key={index} className="hover:text-gray-900 transition-colors">
                {ing.cantidad_display} de {ing.nombre}
                <span className="text-gray-500 ml-1">({ing.kcal.toFixed(0)} kcal)</span>
              </li>
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
            <li key={index} className="hover:text-gray-900 transition-colors">
              {step}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
