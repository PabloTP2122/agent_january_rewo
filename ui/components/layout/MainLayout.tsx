"use client";

import { useState, useCallback } from "react";
import { Canvas } from "./Canvas";
import { ChatPanel } from "./ChatPanel";
import { MobileToggle, type MobileView } from "./MobileToggle";

export interface MainLayoutProps {
  canvasContent: React.ReactNode;
  chatContent: React.ReactNode;
}

export function MainLayout({ canvasContent, chatContent }: MainLayoutProps) {
  const [mobileView, setMobileView] = useState<MobileView>("chat");
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleViewChange = useCallback((newView: MobileView) => {
    if (newView === mobileView) return;

    setIsTransitioning(true);
    // Small delay for exit animation
    setTimeout(() => {
      setMobileView(newView);
      setIsTransitioning(false);
    }, 150);
  }, [mobileView]);

  return (
    <div className="h-screen flex flex-col">
      {/* Mobile: Toggle tabs */}
      <div className="lg:hidden">
        <MobileToggle activeView={mobileView} onToggle={handleViewChange} />
      </div>

      {/* Content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop: Side-by-side layout */}
        <div className="hidden lg:flex w-full">
          <Canvas className="w-2/3">{canvasContent}</Canvas>
          <ChatPanel className="w-1/3">{chatContent}</ChatPanel>
        </div>

        {/* Mobile: Stacked layout with animated toggle */}
        <div className="lg:hidden w-full h-full relative">
          <div
            className={`
              absolute inset-0 transition-all duration-200 ease-out
              ${mobileView === "canvas"
                ? "opacity-100 translate-x-0"
                : "opacity-0 -translate-x-4 pointer-events-none"
              }
              ${isTransitioning ? "opacity-50" : ""}
            `}
          >
            <Canvas className="h-full">{canvasContent}</Canvas>
          </div>
          <div
            className={`
              absolute inset-0 transition-all duration-200 ease-out
              ${mobileView === "chat"
                ? "opacity-100 translate-x-0"
                : "opacity-0 translate-x-4 pointer-events-none"
              }
              ${isTransitioning ? "opacity-50" : ""}
            `}
          >
            <ChatPanel className="h-full">{chatContent}</ChatPanel>
          </div>
        </div>
      </div>
    </div>
  );
}
