"use client";

import type { ShoppingListItem } from "@/lib/types";

export interface ShoppingListProps {
  items: ShoppingListItem[];
}

export function ShoppingList({ items }: ShoppingListProps) {
  return (
    <section
      className="bg-white rounded-2xl p-6 pt-14 mt-16 relative shadow-md animate-fade-slide-up hover:shadow-lg transition-shadow duration-300"
      aria-labelledby="shopping-list-heading"
    >
      <h2
        id="shopping-list-heading"
        className="absolute -top-7 -left-6 bg-purple-600 text-white font-bold text-xl px-6 py-3 rounded-lg shadow-lg transform hover:scale-105 transition-transform duration-200"
      >
        Lista de compras
      </h2>
      <div className="overflow-x-auto">
        <table
          className="w-full text-left border border-gray-300"
          aria-describedby="shopping-list-heading"
        >
          <caption className="sr-only">
            Lista de {items.length} ingredientes para comprar
          </caption>
          <thead className="bg-purple-600 text-white">
            <tr>
              <th scope="col" className="p-3 font-semibold">Alimento</th>
              <th scope="col" className="p-3 font-semibold">Cantidad</th>
            </tr>
          </thead>
          <tbody className="text-gray-900">
            {items.map((item, index) => (
              <tr
                key={index}
                className="border-t border-gray-300 hover:bg-gray-50 transition-colors"
              >
                <td className="p-3">{item.food}</td>
                <td className="p-3 font-medium text-purple-700">{item.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Summary for screen readers */}
      <p className="sr-only">
        Total de {items.length} ingredientes en la lista de compras
      </p>
    </section>
  );
}
