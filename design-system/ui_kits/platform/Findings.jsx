const { Card, SeverityBadge, Tag, Button, AgentChip, ConfidenceMeter } = window.USAPDesignSystem_e8597b;

const FINDINGS = [
  { id: "VF-001", title: "Hardcoded production credential", loc: "src/config.py:14", sev: "critical", score: 9.1, tm: "TM-001", agent: "vuln-scan" },
  { id: "VF-002", title: "SQL string concatenation", loc: "src/db/profile.js:42", sev: "high", score: 7.8, tm: "TM-002", agent: "vuln-scan" },
  { id: "VF-003", title: "Public S3 bucket ACL", loc: "infra/storage.tf:21", sev: "high", score: 7.1, tm: "TM-002", agent: "iac-security" },
  { id: "VF-004", title: "Missing input validation", loc: "src/routes/profile.js:11", sev: "medium", score: 5.4, tm: "TM-001", agent: "vuln-scan" },
  { id: "VF-005", title: "Permissive CORS policy", loc: "src/middleware/cors.js:6", sev: "low", score: 2.4, tm: "UNMAPPED", agent: "vuln-scan" },
];

function Stat({ n, label, tone }) {
  return (
    <Card padding={16} style={{ flex: 1 }}>
      <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 32, color: tone || "var(--ink-50)" }}>{n}</div>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-300)", marginTop: 4 }}>{label}</div>
    </Card>
  );
}

function Findings({ onBack }) {
  const [active, setActive] = React.useState("all");
  const filters = ["all", "critical", "high", "medium", "low"];
  const rows = active === "all" ? FINDINGS : FINDINGS.filter((f) => f.sev === active);

  return (
    <div style={{ height: "100%", overflowY: "auto" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 32px", borderBottom: "1px solid var(--border)", position: "sticky", top: 0, background: "color-mix(in srgb, var(--bg-base) 88%, transparent)", backdropFilter: "var(--blur-md)", zIndex: 5 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Button variant="ghost" size="sm" onClick={onBack}>← Console</Button>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 18, color: "var(--ink-50)" }}>Findings</span>
          <Tag tone="neutral">SimpleStoreAPI</Tag>
        </div>
        <AgentChip name="finding-triage" role="Triage" />
      </header>

      <div style={{ padding: "24px 32px" }}>
        <div style={{ display: "flex", gap: 14, marginBottom: 22 }}>
          <Stat n="5" label="Findings" />
          <Stat n="1" label="Critical" tone="var(--sev-critical)" />
          <Stat n="2" label="High" tone="var(--sev-high)" />
          <Stat n="4 / 5" label="Mapped to TM" tone="var(--cyan-400)" />
        </div>

        {/* filter rail */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {filters.map((f) => (
            <button key={f} onClick={() => setActive(f)} style={{
              fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase",
              padding: "6px 12px", borderRadius: "var(--radius-pill)", cursor: "pointer",
              background: active === f ? "var(--cyan-900)" : "transparent",
              border: `1px solid ${active === f ? "var(--cyan-400)" : "var(--border)"}`,
              color: active === f ? "var(--cyan-200)" : "var(--ink-300)",
            }}>{f}</button>
          ))}
        </div>

        {/* table */}
        <Card padding={0}>
          <div style={{ display: "grid", gridTemplateColumns: "84px 1fr 150px 110px 90px", gap: 0, fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--ink-300)", padding: "12px 18px", borderBottom: "1px solid var(--border)" }}>
            <span>ID</span><span>Finding</span><span>Severity</span><span>Threat</span><span>Score</span>
          </div>
          {rows.map((f, i) => (
            <div key={f.id} style={{ display: "grid", gridTemplateColumns: "84px 1fr 150px 110px 90px", alignItems: "center", gap: 0, padding: "14px 18px", borderBottom: i < rows.length - 1 ? "1px solid var(--line-faint)" : "none" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--cyan-300)" }}>{f.id}</span>
              <div>
                <div style={{ fontFamily: "var(--font-sans)", fontSize: 14, color: "var(--ink-100)" }}>{f.title}</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--ink-300)", marginTop: 2 }}>{f.loc}</div>
              </div>
              <span><SeverityBadge level={f.sev} /></span>
              <span>{f.tm === "UNMAPPED"
                ? <Tag tone="neutral">Unmapped</Tag>
                : <Tag tone="signal">{f.tm}</Tag>}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 14, fontWeight: 600, color: "var(--ink-100)" }}>{f.score}</span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

window.Findings = Findings;
