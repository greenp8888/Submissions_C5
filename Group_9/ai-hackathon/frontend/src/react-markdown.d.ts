declare module "react-markdown" {
  import * as React from "react";

  const ReactMarkdown: React.ComponentType<{
    children?: string;
    className?: string;
    components?: Record<string, React.ComponentType<any> | ((props: any) => React.ReactNode)>;
  }>;

  export default ReactMarkdown;
}

declare module "mermaid" {
  const mermaid: {
    initialize: (config: Record<string, unknown>) => void;
    render: (id: string, text: string) => Promise<{ svg: string }>;
  };

  export default mermaid;
}
