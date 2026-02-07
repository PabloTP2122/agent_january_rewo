// File: ui/lib/config.ts
/**
 * Central configuration for CopilotKit integration.
 */

/** Agent name - must match backend registration */
export const AGENT_NAME = "nutrition_agent" as const;

/** CopilotKit runtime URL (proxied via Next.js API route) */
export const COPILOTKIT_RUNTIME_URL = "/api/copilotkit" as const;

/** Responsive breakpoints (Tailwind defaults) */
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

/** Layout proportions */
export const LAYOUT = {
  canvas_width_percent: 66,
  chat_width_percent: 34,
  mobile_breakpoint: BREAKPOINTS.lg,
} as const;
