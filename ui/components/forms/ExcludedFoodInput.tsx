"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui";

export interface ExcludedFoodInputProps {
  onAdd: (food: string) => void;
}

export function ExcludedFoodInput({ onAdd }: ExcludedFoodInputProps) {
  const [value, setValue] = useState("");

  const handleAdd = useCallback(() => {
    const trimmed = value.trim();
    if (trimmed) {
      onAdd(trimmed);
      setValue("");
    }
  }, [value, onAdd]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ej: gluten, mariscos, nueces..."
        className="
          flex-1 rounded-lg border border-gray-300 px-3 py-2
          text-sm text-gray-900 placeholder:text-gray-400
          focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500
        "
      />
      <Button type="button" variant="outline" size="md" onClick={handleAdd}>
        Agregar
      </Button>
    </div>
  );
}
