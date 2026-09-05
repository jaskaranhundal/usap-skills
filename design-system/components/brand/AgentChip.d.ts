import * as React from "react";

export interface AgentChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** The cs-* agent slug. */
  name?: string;
  /** Optional human-readable role appended after a divider. */
  role?: string | null;
  /** Show the violet "online" indicator. */
  online?: boolean;
}

/** Identity token for a cs-* orchestrator agent — violet dot + mono slug. */
export function AgentChip(props: AgentChipProps): JSX.Element;
