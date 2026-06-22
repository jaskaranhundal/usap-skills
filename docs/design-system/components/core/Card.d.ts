import * as React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Show a cyan signal accent rail across the top edge. */
  accent?: boolean;
  /** Enable hover lift + signal glow (use for clickable cards). */
  interactive?: boolean;
  /** Inner padding in px. */
  padding?: number;
}

/** The default panel surface — dark field, hairline border, subtle lift. */
export function Card(props: CardProps): JSX.Element;
