"use client";

import { forwardRef } from "react";
import type { SelectOption } from "@/lib/constants";

export interface SelectProps<T extends string | number>
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "value" | "onChange"> {
  label: string;
  options: SelectOption<T>[];
  error?: string;
  value?: T;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
}

function SelectInner<T extends string | number>(
  { label, options, error, className = "", id, ...props }: SelectProps<T>,
  ref: React.ForwardedRef<HTMLSelectElement>
) {
  const selectId = id || label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="w-full">
      <label
        htmlFor={selectId}
        className="block text-sm font-medium text-gray-700 mb-1.5"
      >
        {label}
        {props.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <select
        ref={ref}
        id={selectId}
        className={`
          w-full rounded-lg border px-3 py-2
          text-sm text-gray-900
          focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500
          disabled:bg-gray-50 disabled:text-gray-500
          ${error ? "border-red-500 focus:ring-red-200 focus:border-red-500" : "border-gray-300"}
          ${className}
        `}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${selectId}-error` : undefined}
        {...props}
      >
        {options.map((option) => (
          <option key={String(option.value)} value={option.value}>
            {option.label}
            {option.description && ` - ${option.description}`}
          </option>
        ))}
      </select>
      {error && (
        <p id={`${selectId}-error`} className="mt-1 text-sm text-red-500">
          {error}
        </p>
      )}
    </div>
  );
}

export const Select = forwardRef(SelectInner) as <T extends string | number>(
  props: SelectProps<T> & { ref?: React.ForwardedRef<HTMLSelectElement> }
) => React.ReactElement;
