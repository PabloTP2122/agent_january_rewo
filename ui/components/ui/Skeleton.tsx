"use client";

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: "text" | "card" | "table" | "circle" | "badge";
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
    circle: "rounded-full",
    badge: "h-8 rounded-lg",
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height) style.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      className={`
        bg-gray-200 animate-pulse
        ${variants[variant]}
        ${className}
      `}
      style={style}
      role="status"
      aria-label="Loading..."
    />
  );
}

// Convenience components for common skeleton patterns
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading text...">
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
    <div className="bg-white rounded-2xl shadow-md p-6 space-y-4" role="status" aria-label="Loading card...">
      <Skeleton variant="text" width="40%" height={24} />
      <SkeletonText lines={3} />
    </div>
  );
}

// Diet Plan specific skeleton components
export function SkeletonMealCard() {
  return (
    <section
      className="bg-white rounded-2xl p-6 pt-12 mt-16 relative shadow-md animate-pulse"
      role="status"
      aria-label="Loading meal..."
    >
      {/* Meal time badge skeleton */}
      <div className="absolute -top-6 -left-6 bg-gray-300 h-10 w-28 rounded-lg shadow-lg" />

      {/* Title and description */}
      <div className="mb-6 pb-4 border-b border-gray-200">
        <Skeleton variant="text" width="60%" height={28} className="mb-2" />
        <Skeleton variant="text" width="80%" height={20} />
      </div>

      {/* Two columns */}
      <div className="grid md:grid-cols-2 gap-8">
        <div className="space-y-2">
          <Skeleton variant="text" width="40%" height={24} className="mb-3" />
          <Skeleton variant="text" width="90%" />
          <Skeleton variant="text" width="85%" />
          <Skeleton variant="text" width="75%" />
          <Skeleton variant="text" width="80%" />
        </div>
        <div className="space-y-2">
          <Skeleton variant="text" width="40%" height={24} className="mb-3" />
          <Skeleton variant="text" width="70%" />
        </div>
      </div>

      {/* Preparation steps */}
      <div className="mt-6 space-y-2">
        <Skeleton variant="text" width="35%" height={24} className="mb-3" />
        <Skeleton variant="text" width="95%" />
        <Skeleton variant="text" width="90%" />
        <Skeleton variant="text" width="85%" />
      </div>
    </section>
  );
}

export function SkeletonMacrosTable() {
  return (
    <div className="mt-4 space-y-3" role="status" aria-label="Loading macros...">
      {/* Table header skeleton */}
      <div className="grid grid-cols-4 gap-4 pb-2 border-b border-gray-200">
        <Skeleton variant="text" width="70%" height={16} />
        <Skeleton variant="text" width="50%" height={16} />
        <Skeleton variant="text" width="50%" height={16} />
        <Skeleton variant="text" width="60%" height={16} />
      </div>
      {/* Table rows */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="grid grid-cols-4 gap-4">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
          <Skeleton variant="text" width="40%" />
          <div className="h-2 bg-gray-200 rounded-full animate-pulse" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonDietInfoHeader() {
  return (
    <div className="flex items-center gap-4" role="status" aria-label="Loading diet info...">
      <Skeleton variant="badge" width={140} height={32} />
      <Skeleton variant="badge" width={100} height={32} />
    </div>
  );
}

export function SkeletonShoppingList() {
  return (
    <div
      className="bg-white rounded-2xl shadow-md overflow-hidden animate-pulse"
      role="status"
      aria-label="Loading shopping list..."
    >
      {/* Header */}
      <div className="bg-gray-300 px-6 py-4">
        <Skeleton variant="text" width="50%" height={24} className="bg-gray-400" />
      </div>
      {/* Items */}
      <div className="p-6 space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex justify-between items-center">
            <Skeleton variant="text" width="50%" />
            <Skeleton variant="text" width="20%" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonDietPlanCanvas() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading diet plan...">
      {/* Header section */}
      <div className="bg-white rounded-2xl p-6 shadow-md">
        <SkeletonDietInfoHeader />
        <SkeletonMacrosTable />
      </div>

      {/* Meal cards */}
      <SkeletonMealCard />
      <SkeletonMealCard />
      <SkeletonMealCard />

      {/* Shopping list */}
      <SkeletonShoppingList />
    </div>
  );
}
