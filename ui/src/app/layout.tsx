import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Accedemos a la variable de entorno
  const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL;

  return (
    <html lang="es">
      <body>
        <CopilotKit runtimeUrl={runtimeUrl}>
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
