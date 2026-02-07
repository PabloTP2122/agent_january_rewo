"use client";

export type MobileView = "canvas" | "chat";

export interface MobileToggleProps {
  activeView: MobileView;
  onToggle: (view: MobileView) => void;
}

export function MobileToggle({ activeView, onToggle }: MobileToggleProps) {
  return (
    <div className="flex border-b border-gray-200 bg-white">
      <button
        onClick={() => onToggle("canvas")}
        className={`
          flex-1 py-3 text-sm font-medium transition-colors
          ${
            activeView === "canvas"
              ? "text-green-600 border-b-2 border-green-600"
              : "text-gray-500 hover:text-gray-700"
          }
        `}
      >
        <span className="flex items-center justify-center gap-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Plan
        </span>
      </button>
      <button
        onClick={() => onToggle("chat")}
        className={`
          flex-1 py-3 text-sm font-medium transition-colors
          ${
            activeView === "chat"
              ? "text-green-600 border-b-2 border-green-600"
              : "text-gray-500 hover:text-gray-700"
          }
        `}
      >
        <span className="flex items-center justify-center gap-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          Chat
        </span>
      </button>
    </div>
  );
}
