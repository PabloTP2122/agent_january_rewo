"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function Home() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="simple_node_agentui">
      
      <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-zinc-50">
        <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
          <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4">
            Estado del Agente: <span className="font-bold ml-2 text-green-600">Esperando conexión...</span>
          </p>
        </div>

        <div className="mt-10 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            Next.js 16 + LangGraph
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Abre el chat flotante en la esquina inferior derecha para validar que tu nodo
            <code className="mx-2 bg-gray-100 px-2 py-1 rounded text-sm font-semibold">simple_node_agentui</code>
            está respondiendo.
          </p>
        </div>
      </main>

      {/* UI Component: La interfaz de chat pre-construida.
        - instructions: Contexto adicional que se envía al backend (se suma al SystemMessage del grafo).
        - defaultOpen: Se deja en true para probar inmediatamente al cargar.
      */}
      <CopilotPopup
        instructions="Ayuda al usuario a verificar que la conexión técnica funciona."
        labels={{
          title: "Test Agente",
          initial: "Hola, ¿me recibes desde Python?",
        }}
        defaultOpen={true} 
        clickOutsideToClose={false}
      />
      
    </CopilotKit>
  );
}