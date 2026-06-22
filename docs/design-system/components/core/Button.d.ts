import * as React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual weight. `primary` carries the signal-cyan fill + glow. */
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  /** Node rendered before the label (e.g. an icon). */
  iconLeft?: React.ReactNode;
  /** Node rendered after the label. */
  iconRight?: React.ReactNode;
  disabled?: boolean;
  fullWidth?: boolean;
}

/**
 * Primary action control in USAP's HUD voice: mono, uppercase, tracked.
 *
 * @startingPoint section="Core" subtitle="Buttons — primary, secondary, ghost, danger" viewport="700x150"
 */
export function Button(props: ButtonProps): JSX.Element;
