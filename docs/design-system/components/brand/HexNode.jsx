import React from "react";

/**
 * USAP HexNode — the signature hexagonal agent node from the key art.
 * A cyan-outlined hexagon with a HUD label and mono designation. `hub` makes
 * it the glowing central node; default nodes are peripheral.
 */
export function HexNode({
  label = "ALERT TRIAGE",
  designation = "cs-security-analyst",
  hub = false,
  size = 168,
  active = false,
  onClick,
  style = {},
}) {
  const hex = "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)";
  const border = hub || active ? "var(--cyan-400)" : "var(--cyan-700)";
  const glow = hub
    ? "var(--glow-signal-hard)"
    : active
    ? "var(--glow-signal-soft)"
    : "none";
  return (
    <div
      onClick={onClick}
      style={{
        position: "relative",
        width: size,
        height: size * 1.1,
        cursor: onClick ? "pointer" : "default",
        transition: "transform var(--dur-base) var(--ease-signal)",
        ...style,
      }}
      onMouseEnter={(e) => { if (onClick) e.currentTarget.style.transform = "translateY(-3px)"; }}
      onMouseLeave={(e) => { if (onClick) e.currentTarget.style.transform = "translateY(0)"; }}
    >
      {/* outer glow shell */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: hex,
          background: border,
          boxShadow: glow,
        }}
      />
      {/* inner face */}
      <div
        style={{
          position: "absolute",
          inset: hub ? 2 : 1.5,
          clipPath: hex,
          background: hub
            ? "radial-gradient(70% 70% at 50% 45%, var(--cyan-900), var(--void))"
            : "var(--surface-1)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          padding: "0 12%",
          textAlign: "center",
        }}
      >
        {hub ? (
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: size * 0.26,
              letterSpacing: "-0.02em",
              color: "var(--ink-50)",
            }}
          >
            {label}
          </span>
        ) : (
          <>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: size * 0.085,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: active ? "var(--cyan-200)" : "var(--cyan-300)",
                fontWeight: 600,
                lineHeight: 1.2,
              }}
            >
              {label}
            </span>
            {designation && (
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: size * 0.062,
                  letterSpacing: "0.04em",
                  color: "var(--ink-300)",
                }}
              >
                {designation}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
