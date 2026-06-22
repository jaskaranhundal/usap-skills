import * as React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Uppercase mono label above the field. */
  label?: string | null;
  /** Leading prompt glyph in signal cyan, e.g. "$" or ">". */
  prompt?: string | null;
  /** Static prefix text inside the field (muted). */
  prefix?: string | null;
  /** Render the error (red) border state. */
  invalid?: boolean;
  containerStyle?: React.CSSProperties;
}

/** Terminal-style text field — mono, dark well, cyan focus glow. */
export function Input(props: InputProps): JSX.Element;
