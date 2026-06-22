import * as React from "react";

export interface HexNodeProps {
  /** HUD title (or the wordmark text when `hub`). */
  label?: string;
  /** Mono sub-label, e.g. the agent slug. Ignored when `hub`. */
  designation?: string;
  /** Render as the glowing central hub node. */
  hub?: boolean;
  /** Width in px (height derives from it). */
  size?: number;
  /** Highlight as currently-selected. */
  active?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

/**
 * The signature hexagonal agent node from USAP's key art.
 *
 * @startingPoint section="Brand" subtitle="Hexagonal agent node — hub and peripheral" viewport="700x260"
 */
export function HexNode(props: HexNodeProps): JSX.Element;
