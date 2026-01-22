import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";


const runtime = new CopilotRuntime({
  // En v1.50+, usa remoteEndpoints en lugar de un ServiceAdapter para agentes.
  remoteEndpoints: [
    {
      url: process.env.REMOTE_ACTION_URL || "http://127.0.0.1:8000/copilotkit",
    },
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new OpenAIAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};