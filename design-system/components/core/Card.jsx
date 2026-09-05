import React from "react";

/**
 * USAP Card — panel on the dark field. Optional cyan signal accent rail and
 * hoverable lift. The default surface for everything in the platform UI.
 */
export function Card({
  children,
  accent = false,
  interactive = false,
  padding = 20,
  style = {},
  ...rest
}) {
  return (
    <div
      style={{
        position: "relative",
        background: "var(--surface-card)",
        backgroundImage: "var(--grad-surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding,
        boxShadow: "var(--shadow-md)",
        overflow: "hidden",
        transition: "border-color var(--dur-base) var(--ease-signal), box-shadow var(--dur-base) var(--ease-signal), transform var(--dur-base) var(--ease-signal)",
        cursor: interactive ? "pointer" : "default",
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!interactive) return;
        e.currentTarget.style.borderColor = "var(--cyan-700)";
        e.currentTarget.style.boxShadow = "var(--shadow-lg), var(--glow-signal-soft)";
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        if (!interactive) return;
        e.currentTarget.style.borderColor = "var(--border)";
        e.currentTarget.style.boxShadow = "var(--shadow-md)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
      {...rest}
    >
      {accent && (
        <span
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: 2,
            background: "var(--grad-signal)",
            boxShadow: "0 0 12px rgba(41,211,240,0.5)",
          }}
        />
      )}
      {children}
    </div>
  );
}
