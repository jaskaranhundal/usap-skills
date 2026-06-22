const { HexNode, Tag, Button, AgentChip } = window.USAPDesignSystem_e8597b;

function Landing({ onLaunch }) {
  const peripherals = [
    { label: "Alert Triage", designation: "cs-security-analyst", pos: { top: "6%", left: "14%" } },
    { label: "IR Command", designation: "cs-incident-responder", pos: { top: "6%", right: "14%" } },
    { label: "Program Ops", designation: "cs-program-manager", pos: { bottom: "6%", left: "14%" } },
    { label: "Executive Brief", designation: "cs-ciso-advisor", pos: { bottom: "6%", right: "14%" } },
  ];
  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      {/* top bar */}
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 32px", borderBottom: "1px solid var(--border)", position: "relative", zIndex: 2 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 20, color: "var(--ink-50)", letterSpacing: "-0.02em" }}>USA<span style={{ color: "var(--cyan-400)", textShadow: "var(--glow-text)" }}>P</span></span>
          <Tag tone="signal" dot>Open source</Tag>
        </div>
        <nav style={{ display: "flex", alignItems: "center", gap: 24, fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-300)" }}>
          <span>Agents</span><span>Skills</span><span>Docs</span>
          <Button variant="secondary" size="sm" onClick={onLaunch}>Launch console</Button>
        </nav>
      </header>

      {/* hero */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.05fr 1fr", alignItems: "center", gap: 24, padding: "32px 56px", position: "relative", zIndex: 1 }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--cyan-400)", marginBottom: 18 }}>Unified Security Agent Platform</div>
          <h1 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 50, lineHeight: 1.05, letterSpacing: "-0.02em", color: "var(--ink-50)", margin: "0 0 20px" }}>
            Agents reason.<br />Humans approve.<br /><span style={{ color: "var(--cyan-400)", textShadow: "var(--glow-text)" }}>MCP executes.</span>
          </h1>
          <p style={{ fontFamily: "var(--font-sans)", fontSize: 17, lineHeight: 1.55, color: "var(--ink-200)", maxWidth: 460, margin: "0 0 28px" }}>
            An open-source cybersecurity skills library that turns any LLM into an auditable, portable security workflow runtime — mapped to MITRE ATT&CK and NIST CSF 2.0.
          </p>
          <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
            <Button variant="primary" onClick={onLaunch}>Run a scan</Button>
            <Button variant="ghost">View on GitHub →</Button>
          </div>
          <div style={{ display: "flex", gap: 36, fontFamily: "var(--font-mono)" }}>
            {[["79", "Skills"], ["12", "Agents"], ["12", "Domains"]].map(([n, l]) => (
              <div key={l}>
                <div style={{ fontSize: 28, fontWeight: 600, color: "var(--ink-50)", fontFamily: "var(--font-display)" }}>{n}</div>
                <div style={{ fontSize: 10.5, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-300)", marginTop: 2 }}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* hex constellation */}
        <div style={{ position: "relative", height: 440 }}>
          <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", zIndex: 2 }}>
            <HexNode hub label="USAP" size={150} />
          </div>
          {peripherals.map((p, i) => (
            <div key={i} style={{ position: "absolute", ...p.pos, zIndex: 1 }}>
              <HexNode label={p.label} designation={p.designation} size={132} />
            </div>
          ))}
          {/* connective lines */}
          <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 0 }} preserveAspectRatio="none">
            <defs>
              <linearGradient id="ln" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="rgba(41,211,240,0.05)" />
                <stop offset="50%" stopColor="rgba(41,211,240,0.4)" />
                <stop offset="100%" stopColor="rgba(41,211,240,0.05)" />
              </linearGradient>
            </defs>
            <line x1="26%" y1="22%" x2="50%" y2="50%" stroke="url(#ln)" strokeWidth="1.5" strokeDasharray="4 5" />
            <line x1="74%" y1="22%" x2="50%" y2="50%" stroke="url(#ln)" strokeWidth="1.5" strokeDasharray="4 5" />
            <line x1="26%" y1="78%" x2="50%" y2="50%" stroke="url(#ln)" strokeWidth="1.5" strokeDasharray="4 5" />
            <line x1="74%" y1="78%" x2="50%" y2="50%" stroke="url(#ln)" strokeWidth="1.5" strokeDasharray="4 5" />
          </svg>
        </div>
      </div>
    </div>
  );
}

window.Landing = Landing;
