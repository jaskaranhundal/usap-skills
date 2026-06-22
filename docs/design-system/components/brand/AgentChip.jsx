import React from "react";

/**
 * USAP AgentChip — identity token for a cs-* orchestrator agent. Violet dot +
 * mono slug, mirroring the agent color in the demo terminal.
 */
export function AgentChip({ name = "cs-security-analyst", role = null, online = true, style = {}, ...rest }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 9,
        padding: "5px 12px 5px 10px",
        background: "var(--surface-2)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-pill)",
        fontFamily: "var(--font-mono)",
        whiteSpace: "nowrap",
        ...style,
      }}
      {...rest}
    >
      <span style={{ position: "relative", width: 8, height: 8 }}>
        <span
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: online ? "var(--violet-400)" : "var(--ink-400)",
            boxShadow: online ? "0 0 8px var(--violet-400)" : "none",
          }}
        />
      </span>
      <span style={{ color: "var(--violet-400)", fontSize: 12, letterSpacing: "0.02em" }}>{name}</span>
      {role && (
        <span style={{ color: "var(--ink-300)", fontSize: 10.5, letterSpacing: "0.04em", borderLeft: "1px solid var(--line-2)", paddingLeft: 9 }}>
          {role}
        </span>
      )}
    </span>
  );
}
