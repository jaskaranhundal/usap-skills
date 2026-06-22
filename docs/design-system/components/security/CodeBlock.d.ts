import * as React from "react";

export interface CodeBlockProps {
  /** A JSON-serializable object to render with syntax highlighting. */
  data?: unknown;
  /** Filename shown in the terminal header. */
  title?: string;
  /** Raw code content (used when `data` is not provided). */
  children?: React.ReactNode;
  style?: React.CSSProperties;
}

/**
 * Terminal panel with traffic-light chrome and JSON syntax highlighting,
 * matching USAP's demo theme.
 *
 * @startingPoint section="Security" subtitle="Terminal output panel with JSON highlighting" viewport="700x320"
 */
export function CodeBlock(props: CodeBlockProps): JSX.Element;
