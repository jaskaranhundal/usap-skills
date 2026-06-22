import React from "react";

/**
 * USAP CodeBlock — terminal panel with traffic-light header and JSON syntax
 * highlighting matching the brand's demo theme. Pass a JSON-serializable
 * `data` object, or raw `children` for arbitrary code.
 */
export function CodeBlock({ data = null, title = "output.json", children = null, style = {} }) {
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        boxShadow: "var(--shadow-md)",
        fontFamily: "var(--font-mono)",
        ...style,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 7,
          padding: "9px 14px",
          background: "var(--surface-3)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#ff5f57" }} />
        <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#febc2e" }} />
        <span style={{ width: 11, height: 11, borderRadius: "50%", background: "#28c840" }} />
        <span style={{ marginLeft: 8, color: "var(--ink-300)", fontSize: 11.5 }}>{title}</span>
      </div>
      <pre
        style={{
          margin: 0,
          padding: "14px 16px",
          fontSize: 12.5,
          lineHeight: 1.7,
          color: "var(--code-punct)",
          overflowX: "auto",
          whiteSpace: "pre",
        }}
      >
        {data != null ? <JsonView value={data} /> : children}
      </pre>
    </div>
  );
}

function JsonView({ value, indent = 0 }) {
  const pad = "  ".repeat(indent);
  if (Array.isArray(value)) {
    if (value.length === 0) return <span>[]</span>;
    return (
      <>
        <span>[</span>
        {"\n"}
        {value.map((item, i) => (
          <React.Fragment key={i}>
            {pad}{"  "}
            <JsonView value={item} indent={indent + 1} />
            {i < value.length - 1 ? <span style={{ color: "var(--code-punct)" }}>,</span> : null}
            {"\n"}
          </React.Fragment>
        ))}
        {pad}<span>]</span>
      </>
    );
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value);
    return (
      <>
        <span>{"{"}</span>
        {"\n"}
        {keys.map((k, i) => (
          <React.Fragment key={k}>
            {pad}{"  "}
            <span style={{ color: "var(--code-key)" }}>"{k}"</span>
            <span style={{ color: "var(--code-punct)" }}>: </span>
            <JsonView value={value[k]} indent={indent + 1} />
            {i < keys.length - 1 ? <span style={{ color: "var(--code-punct)" }}>,</span> : null}
            {"\n"}
          </React.Fragment>
        ))}
        {pad}<span>{"}"}</span>
      </>
    );
  }
  if (typeof value === "string") return <span style={{ color: "var(--code-string)" }}>"{value}"</span>;
  if (typeof value === "number") return <span style={{ color: "var(--code-number)" }}>{String(value)}</span>;
  if (typeof value === "boolean") return <span style={{ color: "var(--code-number)" }}>{String(value)}</span>;
  if (value === null) return <span style={{ color: "var(--code-comment)" }}>null</span>;
  return <span>{String(value)}</span>;
}
