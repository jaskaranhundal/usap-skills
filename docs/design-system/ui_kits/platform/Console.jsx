const { AgentChip, CodeBlock, ConfidenceMeter, SeverityBadge, Button, Input, Tag } = window.USAPDesignSystem_e8597b;

const PAYLOAD = {
  agent_slug: "vuln-scan",
  intent_type: "detect",
  action: "Hand off to finding-triage — 4 mapped findings, 1 unmapped, top severity high.",
  confidence: 0.82,
  severity: "high",
  next_agents: ["finding-triage"],
  human_approval_required: false,
  timestamp_utc: "2026-06-20T10:30:00Z",
};

// One transcript turn
function Turn({ children }) {
  return <div style={{ marginBottom: 20 }}>{children}</div>;
}
function Speaker({ who, tone }) {
  const c = tone === "user" ? "var(--green-400)" : "var(--violet-400)";
  return <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", color: c, marginBottom: 8 }}>{who}</div>;
}
function Bubble({ children }) {
  return <div style={{ fontFamily: "var(--font-sans)", fontSize: 15, lineHeight: 1.55, color: "var(--ink-100)" }}>{children}</div>;
}

function Console({ onOpenFindings }) {
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

  return (
    <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", height: "100%" }}>
      {/* sidebar */}
      <aside style={{ borderRight: "1px solid var(--border)", background: "var(--surface-1)", padding: "20px 16px", display: "flex", flexDirection: "column", gap: 18 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 17, color: "var(--ink-50)" }}>USA<span style={{ color: "var(--cyan-400)" }}>P</span></span>
          <Tag tone="neutral">Console</Tag>
        </div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-300)", marginBottom: 10 }}>Active agents</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <AgentChip name="cs-appsec-engineer" role="AppSec" />
            <AgentChip name="cs-security-analyst" role="SOC" />
            <AgentChip name="cs-ciso-advisor" online={false} />
          </div>
        </div>
        <div style={{ marginTop: "auto" }}>
          <Button variant="secondary" size="sm" fullWidth onClick={onOpenFindings}>Open findings →</Button>
        </div>
      </aside>

      {/* transcript */}
      <main style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "28px 40px" }}>
          <Turn>
            <Speaker who="you" tone="user" />
            <Bubble>{value}</Bubble>
          </Turn>

          {stage >= 1 && (
            <Turn>
              <Speaker who="cs-appsec-engineer" tone="agent" />
              <Bubble>Running <code style={{ fontFamily: "var(--font-mono)", color: "var(--cyan-300)" }}>vuln-scan</code> against threat model TM-001..TM-005.</Bubble>
            </Turn>
          )}

          {stage === 1 && (
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--ink-300)", display: "flex", alignItems: "center", gap: 8 }}>
              <span className="usap-pulse" style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--cyan-400)" }} />
              scanning…
            </div>
          )}

          {stage >= 2 && (
            <>
              <Turn>
                <CodeBlock title="sample_output.json" data={PAYLOAD} />
              </Turn>
              <Turn>
                <Speaker who="cs-appsec-engineer" tone="agent" />
                <Bubble>
                  Severity is <SeverityBadge level="high" />, <code style={{ fontFamily: "var(--font-mono)", color: "var(--cyan-300)" }}>next_agents</code> points at finding-triage. Handing off.
                </Bubble>
                <div style={{ display: "flex", gap: 24, alignItems: "center", marginTop: 16, flexWrap: "wrap" }}>
                  <div style={{ width: 200 }}><ConfidenceMeter value={0.82} /></div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--ink-300)" }}>
                    <span>HANDOFF</span><span style={{ color: "var(--cyan-400)" }}>→</span><AgentChip name="finding-triage" />
                  </div>
                </div>
              </Turn>
            </>
          )}
        </div>

        {/* composer */}
        <div style={{ borderTop: "1px solid var(--border)", padding: "16px 40px", background: "var(--surface-1)", display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div style={{ flex: 1 }}>
            <Input prompt=">" value={value} onChange={(e) => setValue(e.target.value)} />
          </div>
          <Button variant="primary" onClick={run} disabled={stage !== 0}>{stage === 0 ? "Run" : "Done"}</Button>
        </div>
      </main>
    </div>
  );
}

window.Console = Console;
