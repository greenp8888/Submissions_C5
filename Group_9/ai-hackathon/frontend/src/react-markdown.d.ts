declare module "react-markdown" {
  import * as React from "react";

  const ReactMarkdown: React.ComponentType<{
    children?: string;
    className?: string;
  }>;

  export default ReactMarkdown;
}
