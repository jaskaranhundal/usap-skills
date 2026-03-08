# shared

Utility scripts shared across multiple skill packages.

These are pure Python tools — no external dependencies beyond the standard library.
Each script is self-contained and can be run directly without installing USAP.

---

## Scripts

### `cvss_scorer.py` — CVSS v3.1 base score calculator

Calculates a CVSS v3.1 base score from a vector string. Used by vulnerability-management,
risk-threat-modeling, and any agent that needs to score CVEs.

```bash
# Score a vector string
python shared/scripts/cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"

# Output: {"score": 10.0, "severity": "Critical", "vector": "..."}

# Pipe from stdin
echo "CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:U/C:H/I:H/A:H" | python shared/scripts/cvss_scorer.py
```

**Output fields:**

| Field | Type | Description |
|---|---|---|
| `score` | float (0.0-10.0) | CVSS base score |
| `severity` | string | None / Low / Medium / High / Critical |
| `vector` | string | Normalized vector string |
| `av`, `ac`, `pr`, `ui`, `s`, `c`, `i`, `a` | string | Individual metric values |

**Score to severity mapping:**

| Score | Severity |
|---|---|
| 0.0 | None |
| 0.1 - 3.9 | Low |
| 4.0 - 6.9 | Medium |
| 7.0 - 8.9 | High |
| 9.0 - 10.0 | Critical |

---

### `bb_scope_enforcer.py` — Bug bounty scope enforcement

Validates that a target (IP, domain, URL, CIDR) is within an authorized bug bounty scope.
Returns a structured verdict before any active testing begins.

Intended for use with the `usap-bugbounty` skill packages. Public agents that need
scope validation can import from this script.

```bash
# Check if a target is in scope
python shared/scripts/bb_scope_enforcer.py --target example.com --scope-file scope.json

# Validate a list of targets from stdin
cat targets.txt | python shared/scripts/bb_scope_enforcer.py --scope-file scope.json --batch

# Output: {"target": "example.com", "in_scope": true, "scope_entry": "*.example.com", "verdict": "allowed"}
```

**Scope file format:**

```json
{
  "program": "Example Bug Bounty",
  "in_scope": [
    "*.example.com",
    "192.168.0.0/24",
    "https://api.example.com"
  ],
  "out_of_scope": [
    "admin.example.com",
    "legacy.example.com"
  ]
}
```

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Target is in scope |
| 1 | Target is out of scope |
| 2 | Cannot determine scope (invalid input) |

---

## Usage in SKILL.md prompts

Reference these tools in the Tool Integration section of any SKILL.md:

```bash
# CVSS scoring
python shared/scripts/cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/..."

# Scope enforcement
python shared/scripts/bb_scope_enforcer.py --target <target> --scope-file scope.json
```

---

## Adding shared scripts

A script belongs in `shared/` when:
- It is used by 3 or more skill packages, OR
- It provides core algorithmic capability (scoring, validation, classification) with no skill-specific logic

Scripts used by only one agent belong in that agent's `scripts/` directory.
