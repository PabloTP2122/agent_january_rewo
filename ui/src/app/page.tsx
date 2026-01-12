"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-center font-mono text-sm lg:flex flex-col gap-4">
        <h1 className="text-4xl font-bold text-center">Agent January ReWOO</h1>
        <p className="text-xl text-center">
            Connect your agent to the right panel to start chatting.
        </p>
      </div>

      <CopilotSidebar
        defaultOpen={true}
        instructions="You are a helpful assistant."
        labels={{
            title: "Agent Assistant",
            initial: "Hi! How can I help you today?"
        }}
      />
    </main>
  );
}
