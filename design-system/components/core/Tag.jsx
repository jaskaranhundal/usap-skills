import React from "react";

/**
 * USAP Tag — small mono capsule for metadata: frameworks, levels, "OPEN SOURCE".
 * Quiet by default; `signal` outlines in cyan; `solid` fills.
 */
export function Tag({ children, tone = "neutral", solid = false, dot = false, style = {}, ...rest }) {
  const tones = {
    neutral: { color: "var(--ink-300)", border: "var(--line-2)", fill: "var(--surface-3)", dotc: "var(--ink-300)" },
    signal: { color: "var(--cyan-300)", border: "var(--cyan-700)", fill: "var(--cyan-900)", dotc: "var(--cyan-400)" },
    agent: { color: "var(--violet-400)", border: "color-mix(in srgb, var(--violet-400) 35%, transparent)", fill: "color-mix(in srgb, var(--violet-400) 12%, transparent)", dotc: "var(--violet-400)" },
    ok: { color: "var(--green-400)", border: "color-mix(in srgb, var(--green-400) 35%, transparent)", fill: "color-mix(in srgb, var(--green-400) 12%, transparent)", dotc: "var(--green-400)" },
  };
  const t = tones[tone] || tones.neutral;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "3px 9px",
        fontFamily: "var(--font-mono)",
        fontSize: 10.5,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        borderRadius: "var(--radius-pill)",
        color: solid ? "var(--void)" : t.color,
        background: solid ? t.dotc : t.fill,
        border: `1px solid ${solid ? t.dotc : t.border}`,
        lineHeight: 1.4,
        whiteSpace: "nowrap",
        ...style,
      }}
      {...rest}
    >
      {dot && (
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: solid ? "var(--void)" : t.dotc }} />
      )}
      {children}
    </span>
  );
}
