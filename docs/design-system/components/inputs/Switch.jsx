import React from "react";

/**
 * USAP Switch — approval-gate toggle. On state glows cyan; reads as a hard,
 * deliberate state change (this often gates human_approval_required).
 */
export function Switch({ checked = false, onChange, disabled = false, label = null, style = {} }) {
  const toggle = () => { if (!disabled && onChange) onChange(!checked); };
  return (
    <span
      role="switch"
      aria-checked={checked}
      aria-disabled={disabled}
      onClick={toggle}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        fontFamily: "var(--font-mono)",
        ...style,
      }}
    >
      <span
        style={{
          position: "relative",
          width: 38,
          height: 22,
          borderRadius: "var(--radius-pill)",
          background: checked ? "var(--cyan-900)" : "var(--surface-3)",
          border: `1px solid ${checked ? "var(--cyan-400)" : "var(--line-2)"}`,
          boxShadow: checked ? "var(--glow-signal-soft)" : "none",
          transition: "all var(--dur-base) var(--ease-signal)",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 3,
            left: checked ? 18 : 3,
            width: 14,
            height: 14,
            borderRadius: "50%",
            background: checked ? "var(--cyan-300)" : "var(--ink-300)",
            boxShadow: checked ? "0 0 8px var(--cyan-400)" : "none",
            transition: "all var(--dur-base) var(--ease-signal)",
          }}
        />
      </span>
      {label && (
        <span style={{ color: checked ? "var(--ink-100)" : "var(--ink-300)", fontSize: 12, letterSpacing: "0.04em" }}>
          {label}
        </span>
      )}
    </span>
  );
}
