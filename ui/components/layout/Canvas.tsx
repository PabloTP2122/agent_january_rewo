"use client";

export interface CanvasProps {
  children: React.ReactNode;
  className?: string;
}

export function Canvas({ children, className = "" }: CanvasProps) {
  return (
    <div
      className={`
        h-full overflow-y-auto bg-gray-50 p-6
        ${className}
      `}
    >
      {children}
    </div>
  );
}
