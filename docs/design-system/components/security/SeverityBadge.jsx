import React from "react";

const LEVELS = {
  critical: { c: "var(--sev-critical)", label: "Critical" },
  high: { c: "var(--sev-high)", label: "High" },
  medium: { c: "var(--sev-medium)", label: "Medium" },
  low: { c: "var(--sev-low)", label: "Low" },
  info: { c: "var(--sev-info)", label: "Info" },
};

/**
 * USAP SeverityBadge — CVSS-aligned severity chip. Solid for critical/high to
 * draw the eye; outlined for the rest. Optional CVSS score readout.
 */
export function SeverityBadge({ level = "medium", score = null, style = {}, ...rest }) {
  const l = LEVELS[level] || LEVELS.medium;
  const filled = level === "critical" || level === "high";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 7,
        padding: "3px 9px 3px 8px",
        borderRadius: "var(--radius-sm)",
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        color: filled ? "var(--void)" : l.c,
        background: filled ? l.c : `color-mix(in srgb, ${l.c} 12%, transparent)`,
        border: `1px solid color-mix(in srgb, ${l.c} ${filled ? "100%" : "40%"}, transparent)`,
        lineHeight: 1.3,
        whiteSpace: "nowrap",
        ...style,
      }}
      {...rest}
    >
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: filled ? "var(--void)" : l.c,
          boxShadow: filled ? "none" : `0 0 8px ${l.c}`,
        }}
      />
      {l.label}
      {score != null && (
        <span style={{ opacity: filled ? 0.75 : 0.6, fontWeight: 600 }}>{score}</span>
      )}
    </span>
  );
}
