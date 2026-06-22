import React from "react";

/**
 * USAP Button — HUD control with mono, tracked, uppercase label.
 * Primary carries the signal-cyan fill + glow; others recede into the void.
 */
export function Button({
  children,
  variant = "primary",
  size = "md",
  iconLeft = null,
  iconRight = null,
  disabled = false,
  fullWidth = false,
  type = "button",
  onClick,
  style = {},
  ...rest
}) {
  const sizes = {
    sm: { height: 28, padding: "0 12px", fontSize: 11 },
    md: { height: 36, padding: "0 16px", fontSize: 12 },
    lg: { height: 44, padding: "0 22px", fontSize: 13 },
  };
  const variants = {
    primary: {
      background: "var(--cyan-400)",
      color: "var(--void)",
      border: "1px solid var(--cyan-400)",
      boxShadow: "var(--glow-signal-soft)",
      fontWeight: 600,
    },
    secondary: {
      background: "transparent",
      color: "var(--cyan-300)",
      border: "1px solid var(--cyan-700)",
      boxShadow: "none",
      fontWeight: 500,
    },
    ghost: {
      background: "transparent",
      color: "var(--ink-200)",
      border: "1px solid transparent",
      boxShadow: "none",
      fontWeight: 500,
    },
    danger: {
      background: "transparent",
      color: "var(--red-400)",
      border: "1px solid color-mix(in srgb, var(--red-400) 45%, transparent)",
      boxShadow: "none",
      fontWeight: 500,
    },
  };
  const s = sizes[size] || sizes.md;
  const v = variants[variant] || variants.primary;

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        height: s.height,
        padding: s.padding,
        width: fullWidth ? "100%" : "auto",
        fontFamily: "var(--font-mono)",
        fontSize: s.fontSize,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        borderRadius: "var(--radius-md)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.4 : 1,
        transition: "transform var(--dur-fast) var(--ease-signal), box-shadow var(--dur-base) var(--ease-signal), background var(--dur-base) var(--ease-signal), color var(--dur-base) var(--ease-signal)",
        whiteSpace: "nowrap",
        ...v,
        ...style,
      }}
      onMouseEnter={(e) => {
        if (disabled) return;
        if (variant === "primary") {
          e.currentTarget.style.background = "var(--cyan-300)";
          e.currentTarget.style.boxShadow = "var(--glow-signal-hard)";
        } else if (variant === "secondary") {
          e.currentTarget.style.borderColor = "var(--cyan-400)";
          e.currentTarget.style.color = "var(--cyan-200)";
        } else if (variant === "ghost") {
          e.currentTarget.style.background = "var(--surface-3)";
        } else if (variant === "danger") {
          e.currentTarget.style.background = "color-mix(in srgb, var(--red-400) 12%, transparent)";
        }
      }}
      onMouseLeave={(e) => {
        if (disabled) return;
        Object.assign(e.currentTarget.style, {
          background: v.background,
          color: v.color,
          borderColor: variants[variant].border.includes("transparent") && variant === "ghost" ? "transparent" : undefined,
          boxShadow: v.boxShadow,
        });
        e.currentTarget.style.border = v.border;
      }}
      onMouseDown={(e) => { if (!disabled) e.currentTarget.style.transform = "translateY(1px)"; }}
      onMouseUp={(e) => { if (!disabled) e.currentTarget.style.transform = "translateY(0)"; }}
      {...rest}
    >
      {iconLeft}
      {children}
      {iconRight}
    </button>
  );
}
