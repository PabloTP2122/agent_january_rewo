"use client";

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: "text" | "card" | "table";
  className?: string;
}

export function Skeleton({
  width,
  height,
  variant = "text",
  className = "",
}: SkeletonProps) {
  const variants = {
    text: "h-4 rounded",
    card: "h-48 rounded-2xl",
    table: "h-32 rounded-lg",
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height) style.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      className={`
        animate-pulse bg-gray-200
        ${variants[variant]}
        ${className}
      `}
      style={style}
    />
  );
}

// Convenience components for common skeleton patterns
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? "60%" : "100%"}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6 space-y-4">
      <Skeleton variant="text" width="40%" height={24} />
      <SkeletonText lines={3} />
    </div>
  );
}
