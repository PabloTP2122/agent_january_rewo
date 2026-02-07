"use client";

import { useState } from "react";
import { Canvas } from "./Canvas";
import { ChatPanel } from "./ChatPanel";
import { MobileToggle, type MobileView } from "./MobileToggle";

export interface MainLayoutProps {
  canvasContent: React.ReactNode;
  chatContent: React.ReactNode;
}

export function MainLayout({ canvasContent, chatContent }: MainLayoutProps) {
  const [mobileView, setMobileView] = useState<MobileView>("chat");

  return (
    <div className="h-screen flex flex-col">
      {/* Mobile: Toggle tabs */}
      <div className="lg:hidden">
        <MobileToggle activeView={mobileView} onToggle={setMobileView} />
      </div>

      {/* Content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop: Side-by-side layout */}
        <div className="hidden lg:flex w-full">
          <Canvas className="w-2/3">{canvasContent}</Canvas>
          <ChatPanel className="w-1/3">{chatContent}</ChatPanel>
        </div>

        {/* Mobile: Stacked layout with toggle */}
        <div className="lg:hidden w-full h-full">
          {mobileView === "canvas" ? (
            <Canvas className="h-full">{canvasContent}</Canvas>
          ) : (
            <ChatPanel className="h-full">{chatContent}</ChatPanel>
          )}
        </div>
      </div>
    </div>
  );
}
