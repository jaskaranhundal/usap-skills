import * as React from "react";

export interface ConfidenceMeterProps {
  /** Confidence in [0, 1] — the output-contract `confidence` field. */
  value?: number;
  /** Number of bar segments. */
  segments?: number;
  /** Show the numeric readout (e.g. 0.82). */
  showValue?: boolean;
  /** Caption above the bar. */
  label?: string;
  style?: React.CSSProperties;
}

/** Segmented signal bar for a 0..1 confidence score; color shifts by band. */
export function ConfidenceMeter(props: ConfidenceMeterProps): JSX.Element;
