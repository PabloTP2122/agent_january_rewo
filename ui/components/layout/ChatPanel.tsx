"use client";

export interface ChatPanelProps {
  children: React.ReactNode;
  className?: string;
}

export function ChatPanel({ children, className = "" }: ChatPanelProps) {
  return (
    <div
      className={`
        h-full flex flex-col bg-white border-l border-gray-200
        ${className}
      `}
    >
      {children}
    </div>
  );
}
