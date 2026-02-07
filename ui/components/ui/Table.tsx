"use client";

export interface TableColumn<T> {
  key: keyof T;
  header: string;
  className?: string;
}

export interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  className?: string;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  data,
  className = "",
}: TableProps<T>) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full text-left border border-gray-300">
        <thead className="bg-purple-600 text-white">
          <tr>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={`p-3 font-semibold ${column.className || ""}`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="text-gray-900">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-t border-gray-300">
              {columns.map((column) => (
                <td
                  key={String(column.key)}
                  className={`p-3 ${column.className || ""}`}
                >
                  {String(row[column.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
