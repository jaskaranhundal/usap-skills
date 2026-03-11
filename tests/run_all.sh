#!/usr/bin/env bash
# run_all.sh — Run the USAP LLM test harness for all 3 target skills.
#
# Usage:
#   bash tests/run_all.sh
#
# Environment overrides:
#   MODEL=llama3.2:latest bash tests/run_all.sh
#   OLLAMA_URL=http://gpu-box:11434 bash tests/run_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNNER="${SCRIPT_DIR}/skill_runner.py"

MODEL="${MODEL:-qwen3:latest}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

run_skill() {
    local domain="$1"
    local slug="$2"
    local extra_flags="${3:-}"

    echo ""
    echo "────────────────────────────────────────────────────────────"
    echo "  Running: ${domain}/${slug}"
    echo "────────────────────────────────────────────────────────────"

    # shellcheck disable=SC2086
    if python3 "${RUNNER}" \
        --skill "${slug}" \
        --domain "${domain}" \
        --model "${MODEL}" \
        --ollama-url "${OLLAMA_URL}" \
        ${extra_flags}; then
        PASS_COUNT=$(( PASS_COUNT + 1 ))
        RESULTS+=("PASS  ${domain}/${slug}")
    else
        FAIL_COUNT=$(( FAIL_COUNT + 1 ))
        RESULTS+=("FAIL  ${domain}/${slug}")
    fi
}

# ── Pre-flight: confirm Ollama is reachable ───────────────────────────────────
echo ""
echo "========================================================"
echo "  USAP LLM Test Harness — run_all.sh"
echo "========================================================"
echo "  Model      : ${MODEL}"
echo "  Ollama URL : ${OLLAMA_URL}"
echo ""

if ! curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
    echo "ERROR: Ollama is not reachable at ${OLLAMA_URL}"
    echo "  Start it with: ollama serve"
    echo "  Pull model with: ollama pull ${MODEL}"
    exit 1
fi
echo "  Ollama reachable — proceeding."

# ── Run skills ────────────────────────────────────────────────────────────────

# 1. secrets-exposure — with pre-analysis (exit 2 = critical)
run_skill "detection" "secrets-exposure" "--pre-analysis"

# 2. incident-commander — active LockBit 3.0 ransomware
run_skill "response" "incident-commander"

# 3. enterprise-risk-assessment — board-level risk quantification
run_skill "risk-compliance" "enterprise-risk-assessment"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "========================================================"
echo "  Final Results"
echo "========================================================"
for line in "${RESULTS[@]}"; do
    if [[ "${line}" == PASS* ]]; then
        echo "  ✓  ${line}"
    else
        echo "  ✗  ${line}"
    fi
done
echo ""
echo "  ${PASS_COUNT} PASS  |  ${FAIL_COUNT} FAIL  |  $(( PASS_COUNT + FAIL_COUNT )) total"
echo ""

if [[ "${FAIL_COUNT}" -eq 0 ]]; then
    echo "  All skills passed output contract validation."
    exit 0
else
    echo "  ${FAIL_COUNT} skill(s) failed. Review output above."
    exit 1
fi
