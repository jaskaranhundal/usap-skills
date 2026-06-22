import React from "react";

/**
 * USAP Input — terminal-style field. Mono text, dark well, cyan focus ring.
 * Optional leading prompt glyph and label.
 */
export function Input({
  label = null,
  prompt = null,
  invalid = false,
  prefix = null,
  style = {},
  containerStyle = {},
  ...rest
}) {
  const [focused, setFocused] = React.useState(false);
  const borderColor = invalid
    ? "var(--red-400)"
    : focused
    ? "var(--cyan-400)"
    : "var(--border)";
  return (
    <label style={{ display: "block", fontFamily: "var(--font-mono)", ...containerStyle }}>
      {label && (
        <span style={{ display: "block", color: "var(--ink-300)", fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 7 }}>
          {label}
        </span>
      )}
      <span
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "var(--surface-inset)",
          border: `1px solid ${borderColor}`,
          borderRadius: "var(--radius-md)",
          padding: "0 12px",
          height: 40,
          boxShadow: focused ? "var(--glow-signal), var(--glow-inset)" : "none",
          transition: "border-color var(--dur-base) var(--ease-signal), box-shadow var(--dur-base) var(--ease-signal)",
        }}
      >
        {prompt && <span style={{ color: "var(--cyan-400)", fontSize: 13 }}>{prompt}</span>}
        {prefix && <span style={{ color: "var(--ink-300)", fontSize: 13 }}>{prefix}</span>}
        <input
          onFocus={(e) => { setFocused(true); rest.onFocus && rest.onFocus(e); }}
          onBlur={(e) => { setFocused(false); rest.onBlur && rest.onBlur(e); }}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--ink-100)",
            fontFamily: "var(--font-mono)",
            fontSize: 13,
            letterSpacing: "0.02em",
            ...style,
          }}
          {...rest}
        />
      </span>
    </label>
  );
}
