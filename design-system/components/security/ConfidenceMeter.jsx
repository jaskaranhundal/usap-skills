import React from "react";

/**
 * USAP ConfidenceMeter — 0..1 confidence as a segmented signal bar.
 * Mirrors the `confidence` field in the output contract.
 */
export function ConfidenceMeter({ value = 0.5, segments = 10, showValue = true, label = "Confidence", style = {} }) {
  const v = Math.max(0, Math.min(1, value));
  const lit = Math.round(v * segments);
  const tone = v >= 0.75 ? "var(--green-400)" : v >= 0.45 ? "var(--cyan-400)" : "var(--amber-400)";
  return (
    <div style={{ fontFamily: "var(--font-mono)", ...style }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 7 }}>
        <span style={{ color: "var(--ink-300)", fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase" }}>{label}</span>
        {showValue && <span style={{ color: tone, fontSize: 13, fontWeight: 600 }}>{v.toFixed(2)}</span>}
      </div>
      <div style={{ display: "flex", gap: 3 }}>
        {Array.from({ length: segments }).map((_, i) => (
          <span
            key={i}
            style={{
              flex: 1,
              height: 8,
              borderRadius: 2,
              background: i < lit ? tone : "var(--surface-3)",
              boxShadow: i < lit ? `0 0 8px color-mix(in srgb, ${tone} 60%, transparent)` : "none",
              transition: "background var(--dur-base) var(--ease-signal)",
            }}
          />
        ))}
      </div>
    </div>
  );
}
