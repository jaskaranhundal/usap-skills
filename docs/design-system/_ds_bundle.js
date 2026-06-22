/* @ds-bundle: {"format":3,"namespace":"USAPDesignSystem_e8597b","components":[{"name":"AgentChip","sourcePath":"components/brand/AgentChip.jsx"},{"name":"HexNode","sourcePath":"components/brand/HexNode.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"Input","sourcePath":"components/inputs/Input.jsx"},{"name":"Switch","sourcePath":"components/inputs/Switch.jsx"},{"name":"CodeBlock","sourcePath":"components/security/CodeBlock.jsx"},{"name":"ConfidenceMeter","sourcePath":"components/security/ConfidenceMeter.jsx"},{"name":"SeverityBadge","sourcePath":"components/security/SeverityBadge.jsx"}],"sourceHashes":{"components/brand/AgentChip.jsx":"503544f3a51a","components/brand/HexNode.jsx":"398fc29d1774","components/core/Button.jsx":"4b2c6a79b994","components/core/Card.jsx":"26f32c6a52cb","components/core/Tag.jsx":"7fa00b8324a1","components/inputs/Input.jsx":"f80eb3dba2b3","components/inputs/Switch.jsx":"fb7cf920ec07","components/security/CodeBlock.jsx":"64fde4d66c66","components/security/ConfidenceMeter.jsx":"dcc361dc5b5d","components/security/SeverityBadge.jsx":"a5dfabac5030","ui_kits/platform/Console.jsx":"beb595b386f7","ui_kits/platform/Findings.jsx":"ce063d10c1aa","ui_kits/platform/Landing.jsx":"4c5178da0685"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.USAPDesignSystem_e8597b = window.USAPDesignSystem_e8597b || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/brand/AgentChip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * USAP AgentChip — identity token for a cs-* orchestrator agent. Violet dot +
 * mono slug, mirroring the agent color in the demo terminal.
 */
function AgentChip({
  name = "cs-security-analyst",
  role = null,
  online = true,
  style = {},
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 9,
      padding: "5px 12px 5px 10px",
      background: "var(--surface-2)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-pill)",
      fontFamily: "var(--font-mono)",
      whiteSpace: "nowrap",
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("span", {
    style: {
      position: "relative",
      width: 8,
      height: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      inset: 0,
      borderRadius: "50%",
      background: online ? "var(--violet-400)" : "var(--ink-400)",
      boxShadow: online ? "0 0 8px var(--violet-400)" : "none"
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--violet-400)",
      fontSize: 12,
      letterSpacing: "0.02em"
    }
  }, name), role && /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-300)",
      fontSize: 10.5,
      letterSpacing: "0.04em",
      borderLeft: "1px solid var(--line-2)",
      paddingLeft: 9
    }
  }, role));
}
Object.assign(__ds_scope, { AgentChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/AgentChip.jsx", error: String((e && e.message) || e) }); }

// components/brand/HexNode.jsx
try { (() => {
/**
 * USAP HexNode — the signature hexagonal agent node from the key art.
 * A cyan-outlined hexagon with a HUD label and mono designation. `hub` makes
 * it the glowing central node; default nodes are peripheral.
 */
function HexNode({
  label = "ALERT TRIAGE",
  designation = "cs-security-analyst",
  hub = false,
  size = 168,
  active = false,
  onClick,
  style = {}
}) {
  const hex = "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)";
  const border = hub || active ? "var(--cyan-400)" : "var(--cyan-700)";
  const glow = hub ? "var(--glow-signal-hard)" : active ? "var(--glow-signal-soft)" : "none";
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    style: {
      position: "relative",
      width: size,
      height: size * 1.1,
      cursor: onClick ? "pointer" : "default",
      transition: "transform var(--dur-base) var(--ease-signal)",
      ...style
    },
    onMouseEnter: e => {
      if (onClick) e.currentTarget.style.transform = "translateY(-3px)";
    },
    onMouseLeave: e => {
      if (onClick) e.currentTarget.style.transform = "translateY(0)";
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: 0,
      clipPath: hex,
      background: border,
      boxShadow: glow
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: hub ? 2 : 1.5,
      clipPath: hex,
      background: hub ? "radial-gradient(70% 70% at 50% 45%, var(--cyan-900), var(--void))" : "var(--surface-1)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 6,
      padding: "0 12%",
      textAlign: "center"
    }
  }, hub ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: 700,
      fontSize: size * 0.26,
      letterSpacing: "-0.02em",
      color: "var(--ink-50)"
    }
  }, label) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: size * 0.085,
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      color: active ? "var(--cyan-200)" : "var(--cyan-300)",
      fontWeight: 600,
      lineHeight: 1.2
    }
  }, label), designation && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: size * 0.062,
      letterSpacing: "0.04em",
      color: "var(--ink-300)"
    }
  }, designation))));
}
Object.assign(__ds_scope, { HexNode });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/HexNode.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * USAP Button — HUD control with mono, tracked, uppercase label.
 * Primary carries the signal-cyan fill + glow; others recede into the void.
 */
function Button({
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
    sm: {
      height: 28,
      padding: "0 12px",
      fontSize: 11
    },
    md: {
      height: 36,
      padding: "0 16px",
      fontSize: 12
    },
    lg: {
      height: 44,
      padding: "0 22px",
      fontSize: 13
    }
  };
  const variants = {
    primary: {
      background: "var(--cyan-400)",
      color: "var(--void)",
      border: "1px solid var(--cyan-400)",
      boxShadow: "var(--glow-signal-soft)",
      fontWeight: 600
    },
    secondary: {
      background: "transparent",
      color: "var(--cyan-300)",
      border: "1px solid var(--cyan-700)",
      boxShadow: "none",
      fontWeight: 500
    },
    ghost: {
      background: "transparent",
      color: "var(--ink-200)",
      border: "1px solid transparent",
      boxShadow: "none",
      fontWeight: 500
    },
    danger: {
      background: "transparent",
      color: "var(--red-400)",
      border: "1px solid color-mix(in srgb, var(--red-400) 45%, transparent)",
      boxShadow: "none",
      fontWeight: 500
    }
  };
  const s = sizes[size] || sizes.md;
  const v = variants[variant] || variants.primary;
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    disabled: disabled,
    onClick: onClick,
    style: {
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
      ...style
    },
    onMouseEnter: e => {
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
    },
    onMouseLeave: e => {
      if (disabled) return;
      Object.assign(e.currentTarget.style, {
        background: v.background,
        color: v.color,
        borderColor: variants[variant].border.includes("transparent") && variant === "ghost" ? "transparent" : undefined,
        boxShadow: v.boxShadow
      });
      e.currentTarget.style.border = v.border;
    },
    onMouseDown: e => {
      if (!disabled) e.currentTarget.style.transform = "translateY(1px)";
    },
    onMouseUp: e => {
      if (!disabled) e.currentTarget.style.transform = "translateY(0)";
    }
  }, rest), iconLeft, children, iconRight);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * USAP Card — panel on the dark field. Optional cyan signal accent rail and
 * hoverable lift. The default surface for everything in the platform UI.
 */
function Card({
  children,
  accent = false,
  interactive = false,
  padding = 20,
  style = {},
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
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
      ...style
    },
    onMouseEnter: e => {
      if (!interactive) return;
      e.currentTarget.style.borderColor = "var(--cyan-700)";
      e.currentTarget.style.boxShadow = "var(--shadow-lg), var(--glow-signal-soft)";
      e.currentTarget.style.transform = "translateY(-2px)";
    },
    onMouseLeave: e => {
      if (!interactive) return;
      e.currentTarget.style.borderColor = "var(--border)";
      e.currentTarget.style.boxShadow = "var(--shadow-md)";
      e.currentTarget.style.transform = "translateY(0)";
    }
  }, rest), accent && /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: 0,
      left: 0,
      width: "100%",
      height: 2,
      background: "var(--grad-signal)",
      boxShadow: "0 0 12px rgba(41,211,240,0.5)"
    }
  }), children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * USAP Tag — small mono capsule for metadata: frameworks, levels, "OPEN SOURCE".
 * Quiet by default; `signal` outlines in cyan; `solid` fills.
 */
function Tag({
  children,
  tone = "neutral",
  solid = false,
  dot = false,
  style = {},
  ...rest
}) {
  const tones = {
    neutral: {
      color: "var(--ink-300)",
      border: "var(--line-2)",
      fill: "var(--surface-3)",
      dotc: "var(--ink-300)"
    },
    signal: {
      color: "var(--cyan-300)",
      border: "var(--cyan-700)",
      fill: "var(--cyan-900)",
      dotc: "var(--cyan-400)"
    },
    agent: {
      color: "var(--violet-400)",
      border: "color-mix(in srgb, var(--violet-400) 35%, transparent)",
      fill: "color-mix(in srgb, var(--violet-400) 12%, transparent)",
      dotc: "var(--violet-400)"
    },
    ok: {
      color: "var(--green-400)",
      border: "color-mix(in srgb, var(--green-400) 35%, transparent)",
      fill: "color-mix(in srgb, var(--green-400) 12%, transparent)",
      dotc: "var(--green-400)"
    }
  };
  const t = tones[tone] || tones.neutral;
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
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
      ...style
    }
  }, rest), dot && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: "50%",
      background: solid ? "var(--void)" : t.dotc
    }
  }), children);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/inputs/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * USAP Input — terminal-style field. Mono text, dark well, cyan focus ring.
 * Optional leading prompt glyph and label.
 */
function Input({
  label = null,
  prompt = null,
  invalid = false,
  prefix = null,
  style = {},
  containerStyle = {},
  ...rest
}) {
  const [focused, setFocused] = React.useState(false);
  const borderColor = invalid ? "var(--red-400)" : focused ? "var(--cyan-400)" : "var(--border)";
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "block",
      fontFamily: "var(--font-mono)",
      ...containerStyle
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      color: "var(--ink-300)",
      fontSize: 10.5,
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      marginBottom: 7
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      background: "var(--surface-inset)",
      border: `1px solid ${borderColor}`,
      borderRadius: "var(--radius-md)",
      padding: "0 12px",
      height: 40,
      boxShadow: focused ? "var(--glow-signal), var(--glow-inset)" : "none",
      transition: "border-color var(--dur-base) var(--ease-signal), box-shadow var(--dur-base) var(--ease-signal)"
    }
  }, prompt && /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--cyan-400)",
      fontSize: 13
    }
  }, prompt), prefix && /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-300)",
      fontSize: 13
    }
  }, prefix), /*#__PURE__*/React.createElement("input", _extends({
    onFocus: e => {
      setFocused(true);
      rest.onFocus && rest.onFocus(e);
    },
    onBlur: e => {
      setFocused(false);
      rest.onBlur && rest.onBlur(e);
    },
    style: {
      flex: 1,
      background: "transparent",
      border: "none",
      outline: "none",
      color: "var(--ink-100)",
      fontFamily: "var(--font-mono)",
      fontSize: 13,
      letterSpacing: "0.02em",
      ...style
    }
  }, rest))));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/inputs/Input.jsx", error: String((e && e.message) || e) }); }

// components/inputs/Switch.jsx
try { (() => {
/**
 * USAP Switch — approval-gate toggle. On state glows cyan; reads as a hard,
 * deliberate state change (this often gates human_approval_required).
 */
function Switch({
  checked = false,
  onChange,
  disabled = false,
  label = null,
  style = {}
}) {
  const toggle = () => {
    if (!disabled && onChange) onChange(!checked);
  };
  return /*#__PURE__*/React.createElement("span", {
    role: "switch",
    "aria-checked": checked,
    "aria-disabled": disabled,
    onClick: toggle,
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.45 : 1,
      fontFamily: "var(--font-mono)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "relative",
      width: 38,
      height: 22,
      borderRadius: "var(--radius-pill)",
      background: checked ? "var(--cyan-900)" : "var(--surface-3)",
      border: `1px solid ${checked ? "var(--cyan-400)" : "var(--line-2)"}`,
      boxShadow: checked ? "var(--glow-signal-soft)" : "none",
      transition: "all var(--dur-base) var(--ease-signal)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: 3,
      left: checked ? 18 : 3,
      width: 14,
      height: 14,
      borderRadius: "50%",
      background: checked ? "var(--cyan-300)" : "var(--ink-300)",
      boxShadow: checked ? "0 0 8px var(--cyan-400)" : "none",
      transition: "all var(--dur-base) var(--ease-signal)"
    }
  })), label && /*#__PURE__*/React.createElement("span", {
    style: {
      color: checked ? "var(--ink-100)" : "var(--ink-300)",
      fontSize: 12,
      letterSpacing: "0.04em"
    }
  }, label));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/inputs/Switch.jsx", error: String((e && e.message) || e) }); }

// components/security/CodeBlock.jsx
try { (() => {
/**
 * USAP CodeBlock — terminal panel with traffic-light header and JSON syntax
 * highlighting matching the brand's demo theme. Pass a JSON-serializable
 * `data` object, or raw `children` for arbitrary code.
 */
function CodeBlock({
  data = null,
  title = "output.json",
  children = null,
  style = {}
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-1)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-lg)",
      overflow: "hidden",
      boxShadow: "var(--shadow-md)",
      fontFamily: "var(--font-mono)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 7,
      padding: "9px 14px",
      background: "var(--surface-3)",
      borderBottom: "1px solid var(--border)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 11,
      height: 11,
      borderRadius: "50%",
      background: "#ff5f57"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 11,
      height: 11,
      borderRadius: "50%",
      background: "#febc2e"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 11,
      height: 11,
      borderRadius: "50%",
      background: "#28c840"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 8,
      color: "var(--ink-300)",
      fontSize: 11.5
    }
  }, title)), /*#__PURE__*/React.createElement("pre", {
    style: {
      margin: 0,
      padding: "14px 16px",
      fontSize: 12.5,
      lineHeight: 1.7,
      color: "var(--code-punct)",
      overflowX: "auto",
      whiteSpace: "pre"
    }
  }, data != null ? /*#__PURE__*/React.createElement(JsonView, {
    value: data
  }) : children));
}
function JsonView({
  value,
  indent = 0
}) {
  const pad = "  ".repeat(indent);
  if (Array.isArray(value)) {
    if (value.length === 0) return /*#__PURE__*/React.createElement("span", null, "[]");
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, "["), "\n", value.map((item, i) => /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, pad, "  ", /*#__PURE__*/React.createElement(JsonView, {
      value: item,
      indent: indent + 1
    }), i < value.length - 1 ? /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--code-punct)"
      }
    }, ",") : null, "\n")), pad, /*#__PURE__*/React.createElement("span", null, "]"));
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value);
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, "{"), "\n", keys.map((k, i) => /*#__PURE__*/React.createElement(React.Fragment, {
      key: k
    }, pad, "  ", /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--code-key)"
      }
    }, "\"", k, "\""), /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--code-punct)"
      }
    }, ": "), /*#__PURE__*/React.createElement(JsonView, {
      value: value[k],
      indent: indent + 1
    }), i < keys.length - 1 ? /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--code-punct)"
      }
    }, ",") : null, "\n")), pad, /*#__PURE__*/React.createElement("span", null, "}"));
  }
  if (typeof value === "string") return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--code-string)"
    }
  }, "\"", value, "\"");
  if (typeof value === "number") return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--code-number)"
    }
  }, String(value));
  if (typeof value === "boolean") return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--code-number)"
    }
  }, String(value));
  if (value === null) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--code-comment)"
    }
  }, "null");
  return /*#__PURE__*/React.createElement("span", null, String(value));
}
Object.assign(__ds_scope, { CodeBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/security/CodeBlock.jsx", error: String((e && e.message) || e) }); }

// components/security/ConfidenceMeter.jsx
try { (() => {
/**
 * USAP ConfidenceMeter — 0..1 confidence as a segmented signal bar.
 * Mirrors the `confidence` field in the output contract.
 */
function ConfidenceMeter({
  value = 0.5,
  segments = 10,
  showValue = true,
  label = "Confidence",
  style = {}
}) {
  const v = Math.max(0, Math.min(1, value));
  const lit = Math.round(v * segments);
  const tone = v >= 0.75 ? "var(--green-400)" : v >= 0.45 ? "var(--cyan-400)" : "var(--amber-400)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
      marginBottom: 7
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-300)",
      fontSize: 10.5,
      letterSpacing: "0.1em",
      textTransform: "uppercase"
    }
  }, label), showValue && /*#__PURE__*/React.createElement("span", {
    style: {
      color: tone,
      fontSize: 13,
      fontWeight: 600
    }
  }, v.toFixed(2))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 3
    }
  }, Array.from({
    length: segments
  }).map((_, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    style: {
      flex: 1,
      height: 8,
      borderRadius: 2,
      background: i < lit ? tone : "var(--surface-3)",
      boxShadow: i < lit ? `0 0 8px color-mix(in srgb, ${tone} 60%, transparent)` : "none",
      transition: "background var(--dur-base) var(--ease-signal)"
    }
  }))));
}
Object.assign(__ds_scope, { ConfidenceMeter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/security/ConfidenceMeter.jsx", error: String((e && e.message) || e) }); }

// components/security/SeverityBadge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const LEVELS = {
  critical: {
    c: "var(--sev-critical)",
    label: "Critical"
  },
  high: {
    c: "var(--sev-high)",
    label: "High"
  },
  medium: {
    c: "var(--sev-medium)",
    label: "Medium"
  },
  low: {
    c: "var(--sev-low)",
    label: "Low"
  },
  info: {
    c: "var(--sev-info)",
    label: "Info"
  }
};

/**
 * USAP SeverityBadge — CVSS-aligned severity chip. Solid for critical/high to
 * draw the eye; outlined for the rest. Optional CVSS score readout.
 */
function SeverityBadge({
  level = "medium",
  score = null,
  style = {},
  ...rest
}) {
  const l = LEVELS[level] || LEVELS.medium;
  const filled = level === "critical" || level === "high";
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
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
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 7,
      height: 7,
      borderRadius: "50%",
      background: filled ? "var(--void)" : l.c,
      boxShadow: filled ? "none" : `0 0 8px ${l.c}`
    }
  }), l.label, score != null && /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: filled ? 0.75 : 0.6,
      fontWeight: 600
    }
  }, score));
}
Object.assign(__ds_scope, { SeverityBadge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/security/SeverityBadge.jsx", error: String((e && e.message) || e) }); }

// ui_kits/platform/Console.jsx
try { (() => {
const {
  AgentChip,
  CodeBlock,
  ConfidenceMeter,
  SeverityBadge,
  Button,
  Input,
  Tag
} = window.USAPDesignSystem_e8597b;
const PAYLOAD = {
  agent_slug: "vuln-scan",
  intent_type: "detect",
  action: "Hand off to finding-triage — 4 mapped findings, 1 unmapped, top severity high.",
  confidence: 0.82,
  severity: "high",
  next_agents: ["finding-triage"],
  human_approval_required: false,
  timestamp_utc: "2026-06-20T10:30:00Z"
};

// One transcript turn
function Turn({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 20
    }
  }, children);
}
function Speaker({
  who,
  tone
}) {
  const c = tone === "user" ? "var(--green-400)" : "var(--violet-400)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      letterSpacing: "0.08em",
      color: c,
      marginBottom: 8
    }
  }, who);
}
function Bubble({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 15,
      lineHeight: 1.55,
      color: "var(--ink-100)"
    }
  }, children);
}
function Console({
  onOpenFindings
}) {
  const [stage, setStage] = React.useState(0); // 0 prompt, 1 running, 2 done
  const [value, setValue] = React.useState("Scan examples/SimpleStoreAPI and route any high findings to triage.");
  const scrollRef = React.useRef(null);
  const run = () => {
    if (stage === 0) {
      setStage(1);
      setTimeout(() => setStage(2), 1100);
    }
  };
  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [stage]);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "260px 1fr",
      height: "100%"
    }
  }, /*#__PURE__*/React.createElement("aside", {
    style: {
      borderRight: "1px solid var(--border)",
      background: "var(--surface-1)",
      padding: "20px 16px",
      display: "flex",
      flexDirection: "column",
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: 700,
      fontSize: 17,
      color: "var(--ink-50)"
    }
  }, "USA", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--cyan-400)"
    }
  }, "P")), /*#__PURE__*/React.createElement(Tag, {
    tone: "neutral"
  }, "Console")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      letterSpacing: "0.12em",
      textTransform: "uppercase",
      color: "var(--ink-300)",
      marginBottom: 10
    }
  }, "Active agents"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(AgentChip, {
    name: "cs-appsec-engineer",
    role: "AppSec"
  }), /*#__PURE__*/React.createElement(AgentChip, {
    name: "cs-security-analyst",
    role: "SOC"
  }), /*#__PURE__*/React.createElement(AgentChip, {
    name: "cs-ciso-advisor",
    online: false
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "auto"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    fullWidth: true,
    onClick: onOpenFindings
  }, "Open findings \u2192"))), /*#__PURE__*/React.createElement("main", {
    style: {
      display: "flex",
      flexDirection: "column",
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    ref: scrollRef,
    style: {
      flex: 1,
      overflowY: "auto",
      padding: "28px 40px"
    }
  }, /*#__PURE__*/React.createElement(Turn, null, /*#__PURE__*/React.createElement(Speaker, {
    who: "you",
    tone: "user"
  }), /*#__PURE__*/React.createElement(Bubble, null, value)), stage >= 1 && /*#__PURE__*/React.createElement(Turn, null, /*#__PURE__*/React.createElement(Speaker, {
    who: "cs-appsec-engineer",
    tone: "agent"
  }), /*#__PURE__*/React.createElement(Bubble, null, "Running ", /*#__PURE__*/React.createElement("code", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--cyan-300)"
    }
  }, "vuln-scan"), " against threat model TM-001..TM-005.")), stage === 1 && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      color: "var(--ink-300)",
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "usap-pulse",
    style: {
      width: 8,
      height: 8,
      borderRadius: "50%",
      background: "var(--cyan-400)"
    }
  }), "scanning\u2026"), stage >= 2 && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Turn, null, /*#__PURE__*/React.createElement(CodeBlock, {
    title: "sample_output.json",
    data: PAYLOAD
  })), /*#__PURE__*/React.createElement(Turn, null, /*#__PURE__*/React.createElement(Speaker, {
    who: "cs-appsec-engineer",
    tone: "agent"
  }), /*#__PURE__*/React.createElement(Bubble, null, "Severity is ", /*#__PURE__*/React.createElement(SeverityBadge, {
    level: "high"
  }), ", ", /*#__PURE__*/React.createElement("code", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--cyan-300)"
    }
  }, "next_agents"), " points at finding-triage. Handing off."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 24,
      alignItems: "center",
      marginTop: 16,
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 200
    }
  }, /*#__PURE__*/React.createElement(ConfidenceMeter, {
    value: 0.82
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      color: "var(--ink-300)"
    }
  }, /*#__PURE__*/React.createElement("span", null, "HANDOFF"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--cyan-400)"
    }
  }, "\u2192"), /*#__PURE__*/React.createElement(AgentChip, {
    name: "finding-triage"
  })))))), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: "1px solid var(--border)",
      padding: "16px 40px",
      background: "var(--surface-1)",
      display: "flex",
      gap: 12,
      alignItems: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(Input, {
    prompt: ">",
    value: value,
    onChange: e => setValue(e.target.value)
  })), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: run,
    disabled: stage !== 0
  }, stage === 0 ? "Run" : "Done"))));
}
window.Console = Console;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/platform/Console.jsx", error: String((e && e.message) || e) }); }

// ui_kits/platform/Findings.jsx
try { (() => {
const {
  Card,
  SeverityBadge,
  Tag,
  Button,
  AgentChip,
  ConfidenceMeter
} = window.USAPDesignSystem_e8597b;
const FINDINGS = [{
  id: "VF-001",
  title: "Hardcoded production credential",
  loc: "src/config.py:14",
  sev: "critical",
  score: 9.1,
  tm: "TM-001",
  agent: "vuln-scan"
}, {
  id: "VF-002",
  title: "SQL string concatenation",
  loc: "src/db/profile.js:42",
  sev: "high",
  score: 7.8,
  tm: "TM-002",
  agent: "vuln-scan"
}, {
  id: "VF-003",
  title: "Public S3 bucket ACL",
  loc: "infra/storage.tf:21",
  sev: "high",
  score: 7.1,
  tm: "TM-002",
  agent: "iac-security"
}, {
  id: "VF-004",
  title: "Missing input validation",
  loc: "src/routes/profile.js:11",
  sev: "medium",
  score: 5.4,
  tm: "TM-001",
  agent: "vuln-scan"
}, {
  id: "VF-005",
  title: "Permissive CORS policy",
  loc: "src/middleware/cors.js:6",
  sev: "low",
  score: 2.4,
  tm: "UNMAPPED",
  agent: "vuln-scan"
}];
function Stat({
  n,
  label,
  tone
}) {
  return /*#__PURE__*/React.createElement(Card, {
    padding: 16,
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: 700,
      fontSize: 32,
      color: tone || "var(--ink-50)"
    }
  }, n), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      letterSpacing: "0.12em",
      textTransform: "uppercase",
      color: "var(--ink-300)",
      marginTop: 4
    }
  }, label));
}
function Findings({
  onBack
}) {
  const [active, setActive] = React.useState("all");
  const filters = ["all", "critical", "high", "medium", "low"];
  const rows = active === "all" ? FINDINGS : FINDINGS.filter(f => f.sev === active);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100%",
      overflowY: "auto"
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "18px 32px",
      borderBottom: "1px solid var(--border)",
      position: "sticky",
      top: 0,
      background: "color-mix(in srgb, var(--bg-base) 88%, transparent)",
      backdropFilter: "var(--blur-md)",
      zIndex: 5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    onClick: onBack
  }, "\u2190 Console"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: 600,
      fontSize: 18,
      color: "var(--ink-50)"
    }
  }, "Findings"), /*#__PURE__*/React.createElement(Tag, {
    tone: "neutral"
  }, "SimpleStoreAPI")), /*#__PURE__*/React.createElement(AgentChip, {
    name: "finding-triage",
    role: "Triage"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "24px 32px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 22
    }
  }, /*#__PURE__*/React.createElement(Stat, {
    n: "5",
    label: "Findings"
  }), /*#__PURE__*/React.createElement(Stat, {
    n: "1",
    label: "Critical",
    tone: "var(--sev-critical)"
  }), /*#__PURE__*/React.createElement(Stat, {
    n: "2",
    label: "High",
    tone: "var(--sev-high)"
  }), /*#__PURE__*/React.createElement(Stat, {
    n: "4 / 5",
    label: "Mapped to TM",
    tone: "var(--cyan-400)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginBottom: 16
    }
  }, filters.map(f => /*#__PURE__*/React.createElement("button", {
    key: f,
    onClick: () => setActive(f),
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      letterSpacing: "0.06em",
      textTransform: "uppercase",
      padding: "6px 12px",
      borderRadius: "var(--radius-pill)",
      cursor: "pointer",
      background: active === f ? "var(--cyan-900)" : "transparent",
      border: `1px solid ${active === f ? "var(--cyan-400)" : "var(--border)"}`,
      color: active === f ? "var(--cyan-200)" : "var(--ink-300)"
    }
  }, f))), /*#__PURE__*/React.createElement(Card, {
    padding: 0
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "84px 1fr 150px 110px 90px",
      gap: 0,
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      color: "var(--ink-300)",
      padding: "12px 18px",
      borderBottom: "1px solid var(--border)"
    }
  }, /*#__PURE__*/React.createElement("span", null, "ID"), /*#__PURE__*/React.createElement("span", null, "Finding"), /*#__PURE__*/React.createElement("span", null, "Severity"), /*#__PURE__*/React.createElement("span", null, "Threat"), /*#__PURE__*/React.createElement("span", null, "Score")), rows.map((f, i) => /*#__PURE__*/React.createElement("div", {
    key: f.id,
    style: {
      display: "grid",
      gridTemplateColumns: "84px 1fr 150px 110px 90px",
      alignItems: "center",
      gap: 0,
      padding: "14px 18px",
      borderBottom: i < rows.length - 1 ? "1px solid var(--line-faint)" : "none"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      color: "var(--cyan-300)"
    }
  }, f.id), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 14,
      color: "var(--ink-100)"
    }
  }, f.title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      color: "var(--ink-300)",
      marginTop: 2
    }
  }, f.loc)), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement(SeverityBadge, {
    level: f.sev
  })), /*#__PURE__*/React.createElement("span", null, f.tm === "UNMAPPED" ? /*#__PURE__*/React.createElement(Tag, {
    tone: "neutral"
  }, "Unmapped") : /*#__PURE__*/React.createElement(Tag, {
    tone: "signal"
  }, f.tm)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 14,
      fontWeight: 600,
      color: "var(--ink-100)"
    }
  }, f.score))))));
}
window.Findings = Findings;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/platform/Findings.jsx", error: String((e && e.message) || e) }); }

// ui_kits/platform/Landing.jsx
try { (() => {
const {
  HexNode,
  Tag,
  Button,
  AgentChip
} = window.USAPDesignSystem_e8597b;
function Landing({
  onLaunch
}) {
  const peripherals = [{
    label: "Alert Triage",
    designation: "cs-security-analyst",
    pos: {
      top: "6%",
      left: "14%"
    }
  }, {
    label: "IR Command",
    designation: "cs-incident-responder",
    pos: {
      top: "6%",
      right: "14%"
    }
  }, {
    label: "Program Ops",
    designation: "cs-program-manager",
    pos: {
      bottom: "6%",
      left: "14%"
    }
  }, {
    label: "Executive Brief",
    designation: "cs-ciso-advisor",
    pos: {
      bottom: "6%",
      right: "14%"
    }
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: "100%",
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "18px 32px",
      borderBottom: "1px solid var(--border)",
      position: "relative",
      zIndex: 2
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: 700,
      fontSize: 20,
      color: "var(--ink-50)",
      letterSpacing: "-0.02em"
    }
  }, "USA", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--cyan-400)",
      textShadow: "var(--glow-text)"
    }
  }, "P")), /*#__PURE__*/React.createElement(Tag, {
    tone: "signal",
    dot: true
  }, "Open source")), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 24,
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      color: "var(--ink-300)"
    }
  }, /*#__PURE__*/React.createElement("span", null, "Agents"), /*#__PURE__*/React.createElement("span", null, "Skills"), /*#__PURE__*/React.createElement("span", null, "Docs"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    onClick: onLaunch
  }, "Launch console"))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: "grid",
      gridTemplateColumns: "1.05fr 1fr",
      alignItems: "center",
      gap: 24,
      padding: "32px 56px",
      position: "relative",
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      letterSpacing: "0.14em",
      textTransform: "uppercase",
      color: "var(--cyan-400)",
      marginBottom: 18
    }
  }, "Unified Security Agent Platform"), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: 700,
      fontSize: 50,
      lineHeight: 1.05,
      letterSpacing: "-0.02em",
      color: "var(--ink-50)",
      margin: "0 0 20px"
    }
  }, "Agents reason.", /*#__PURE__*/React.createElement("br", null), "Humans approve.", /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--cyan-400)",
      textShadow: "var(--glow-text)"
    }
  }, "MCP executes.")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 17,
      lineHeight: 1.55,
      color: "var(--ink-200)",
      maxWidth: 460,
      margin: "0 0 28px"
    }
  }, "An open-source cybersecurity skills library that turns any LLM into an auditable, portable security workflow runtime \u2014 mapped to MITRE ATT&CK and NIST CSF 2.0."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12,
      marginBottom: 32
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    onClick: onLaunch
  }, "Run a scan"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost"
  }, "View on GitHub \u2192")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 36,
      fontFamily: "var(--font-mono)"
    }
  }, [["79", "Skills"], ["12", "Agents"], ["12", "Domains"]].map(([n, l]) => /*#__PURE__*/React.createElement("div", {
    key: l
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 28,
      fontWeight: 600,
      color: "var(--ink-50)",
      fontFamily: "var(--font-display)"
    }
  }, n), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      letterSpacing: "0.12em",
      textTransform: "uppercase",
      color: "var(--ink-300)",
      marginTop: 2
    }
  }, l))))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      height: 440
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%,-50%)",
      zIndex: 2
    }
  }, /*#__PURE__*/React.createElement(HexNode, {
    hub: true,
    label: "USAP",
    size: 150
  })), peripherals.map((p, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      position: "absolute",
      ...p.pos,
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement(HexNode, {
    label: p.label,
    designation: p.designation,
    size: 132
  }))), /*#__PURE__*/React.createElement("svg", {
    style: {
      position: "absolute",
      inset: 0,
      width: "100%",
      height: "100%",
      zIndex: 0
    },
    preserveAspectRatio: "none"
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: "ln",
    x1: "0",
    y1: "0",
    x2: "1",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0%",
    stopColor: "rgba(41,211,240,0.05)"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "50%",
    stopColor: "rgba(41,211,240,0.4)"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "100%",
    stopColor: "rgba(41,211,240,0.05)"
  }))), /*#__PURE__*/React.createElement("line", {
    x1: "26%",
    y1: "22%",
    x2: "50%",
    y2: "50%",
    stroke: "url(#ln)",
    strokeWidth: "1.5",
    strokeDasharray: "4 5"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "74%",
    y1: "22%",
    x2: "50%",
    y2: "50%",
    stroke: "url(#ln)",
    strokeWidth: "1.5",
    strokeDasharray: "4 5"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "26%",
    y1: "78%",
    x2: "50%",
    y2: "50%",
    stroke: "url(#ln)",
    strokeWidth: "1.5",
    strokeDasharray: "4 5"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "74%",
    y1: "78%",
    x2: "50%",
    y2: "50%",
    stroke: "url(#ln)",
    strokeWidth: "1.5",
    strokeDasharray: "4 5"
  })))));
}
window.Landing = Landing;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/platform/Landing.jsx", error: String((e && e.message) || e) }); }

__ds_ns.AgentChip = __ds_scope.AgentChip;

__ds_ns.HexNode = __ds_scope.HexNode;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.CodeBlock = __ds_scope.CodeBlock;

__ds_ns.ConfidenceMeter = __ds_scope.ConfidenceMeter;

__ds_ns.SeverityBadge = __ds_scope.SeverityBadge;

})();
