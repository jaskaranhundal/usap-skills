import * as React from "react";

export interface SeverityBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** CVSS severity bucket. */
  level?: "critical" | "high" | "medium" | "low" | "info";
  /** Optional CVSS base score rendered alongside the label, e.g. 9.1. */
  score?: number | string | null;
}

/**
 * CVSS-aligned severity chip — solid for critical/high, outlined otherwise.
 *
 * @startingPoint section="Security" subtitle="Severity chips across the CVSS scale" viewport="700x120"
 */
export function SeverityBadge(props: SeverityBadgeProps): JSX.Element;
