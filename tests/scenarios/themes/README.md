# Themed Scenario Harness

Additive scenario library for USAP cs-* agent exercises. Each scenario is a
self-contained YAML file describing a realistic, hour-by-hour security
incident that a SOC engineer can run as a tabletop or that
`cs-purple-team-lead` can walk through as an Attack Chain Walkthrough (`AC`)
or Purple Tabletop (`PT`).

The existing flat JSON scenarios in `tests/scenarios/*.json` are unchanged
and remain the canonical multi-agent regression suite. This directory adds
a themed layer on top of them so that exercises can be grouped, indexed,
and discovered by theme.

## Layout

```
tests/scenarios/themes/
├── README.md               # this file
├── index.yaml              # manifest of themes and scenarios
├── ransomware/             # one directory per theme id
│   └── 2026-q3-fintech-ransomware.yaml
├── supply-chain/
│   └── 2026-q3-npm-malicious-dep.yaml
└── cloud-misconfig/
    └── 2026-q3-iam-overpermission.yaml
```

## Manifest format (`index.yaml`)

```yaml
version: 1
themes:
  - id: <theme-id>
    description: <one-line theme summary>
    scenarios:
      - scenario_id: <unique-slug>
        file: <theme-id>/<filename>.yaml
```

- `id` is the theme slug; one directory per theme.
- `scenario_id` is globally unique across all themes.
- `file` is the relative path under `tests/scenarios/themes/`.

## Scenario format

Every scenario YAML file must contain these top-level keys:

| Key | Type | Notes |
|---|---|---|
| `id` | string | Must match the `scenario_id` in the manifest |
| `theme` | string | Must match an `id` in the manifest |
| `severity` | string | `critical`, `high`, `medium`, `low`, or `informational` |
| `initial_event` | string | One realistic paragraph framing the incident |
| `prerequisites_unverified` | array[string] | Fields the agent must NOT assume |
| `timeline` | array[object] | Each entry: `t:` (e.g. `T+0min`) and `event:` |
| `target_agents` | array[string] | Sub-agents expected to be invoked |
| `expected_outputs` | array[string] | Observable artifacts the run must produce |
| `evaluation_criteria.pass` | array[string] | Pass criteria |
| `evaluation_criteria.fail` | array[string] | Fail criteria (anti-patterns) |

### `prerequisites_unverified`

The most important field for purple-team work. Lists every fact the agent
might be tempted to assume. The agent must explicitly mark each one as
verified or unverified before issuing a recommendation. Forces the
"three voices, one verdict" discipline that `cs-purple-team-lead` enforces.

### `evaluation_criteria.fail`

Anti-patterns. If any one fires, the exercise is a fail regardless of how
many pass criteria match. Designed to catch confident-but-wrong outputs.

## Running a scenario

The harness is documentation-driven; there is no runner script. To run a
scenario, an operator (human or an upstream agent) loads the YAML and feeds
it to `cs-purple-team-lead` with one of the four command codes:

```bash
# Purple Tabletop
cat tests/scenarios/themes/ransomware/2026-q3-fintech-ransomware.yaml
# Then trigger cs-purple-team-lead with code: PT
```

The agent must:
1. Echo the `initial_event` and `prerequisites_unverified` block.
2. Invoke at least two sub-agents from `target_agents`.
3. Produce all items in `expected_outputs`.
4. Self-score against `evaluation_criteria.pass` and
   `evaluation_criteria.fail`.

## Adding a new theme

1. Choose a kebab-case `<theme-id>`.
2. Create `tests/scenarios/themes/<theme-id>/`.
3. Add at least one scenario YAML in the format above.
4. Append a new `themes:` entry to `index.yaml` referencing the file.
5. Validate with:

   ```bash
   python3 -c "import yaml, sys; [yaml.safe_load(open(p)) for p in sys.argv[1:]]" \
     tests/scenarios/themes/index.yaml \
     tests/scenarios/themes/<theme-id>/*.yaml
   ```

## Adding a new scenario to an existing theme

1. Drop a new YAML under `tests/scenarios/themes/<existing-theme-id>/`
   using a `YYYY-qN-<slug>` filename convention.
2. Append a new `scenarios:` entry under that theme in `index.yaml`.
3. Validate as above.

## Relationship to flat scenarios

`tests/scenarios/*.json` (the flat layer) holds the original regression
scenarios pinned for cross-version comparison. They must not be modified.
Themed scenarios are additive and meant for exploratory exercises, where
new tabletop content is added quarterly without disturbing the regression
baseline.
