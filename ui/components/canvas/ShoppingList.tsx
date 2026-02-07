"use client";

import type { ShoppingListItem } from "@/lib/types";

export interface ShoppingListProps {
  items: ShoppingListItem[];
}

export function ShoppingList({ items }: ShoppingListProps) {
  return (
    <section className="bg-white rounded-2xl p-6 pt-14 mt-16 relative shadow-md">
      <div className="absolute -top-7 -left-6 bg-purple-600 text-white font-bold text-xl px-6 py-3 rounded-lg shadow-lg">
        Lista de compras
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border border-gray-300">
          <thead className="bg-purple-600 text-white">
            <tr>
              <th className="p-3 font-semibold">Alimento</th>
              <th className="p-3 font-semibold">Cantidad</th>
            </tr>
          </thead>
          <tbody className="text-gray-900">
            {items.map((item, index) => (
              <tr key={index} className="border-t border-gray-300">
                <td className="p-3">{item.food}</td>
                <td className="p-3">{item.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
