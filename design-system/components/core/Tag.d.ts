import * as React from "react";

export interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Color treatment. */
  tone?: "neutral" | "signal" | "agent" | "ok";
  /** Fill the capsule instead of outlining it. */
  solid?: boolean;
  /** Show a leading status dot. */
  dot?: boolean;
}

/** Small mono capsule for metadata — frameworks, autonomy levels, status flags. */
export function Tag(props: TagProps): JSX.Element;
