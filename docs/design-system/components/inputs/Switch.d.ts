import * as React from "react";

export interface SwitchProps {
  checked?: boolean;
  onChange?: (next: boolean) => void;
  disabled?: boolean;
  /** Optional trailing label. */
  label?: string | null;
  style?: React.CSSProperties;
}

/** Toggle for binary/approval states — on glows cyan. */
export function Switch(props: SwitchProps): JSX.Element;
