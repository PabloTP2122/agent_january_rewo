"use client";

export interface BadgeProps {
  variant?: "success" | "warning" | "error" | "info" | "default";
  size?: "sm" | "md";
  children: React.ReactNode;
  className?: string;
}

export function Badge({
  variant = "default",
  size = "md",
  children,
  className = "",
}: BadgeProps) {
  const variants = {
    success: "bg-green-500 text-white",
    warning: "bg-yellow-500 text-white",
    error: "bg-red-500 text-white",
    info: "bg-blue-500 text-white",
    default: "bg-gray-200 text-gray-800",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
  };

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-lg
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}
