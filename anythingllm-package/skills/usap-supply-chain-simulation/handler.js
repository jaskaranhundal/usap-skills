// AnythingLLM Custom Agent Skill
// USAP: Supply Chain Simulation
// Domain: appsec-devsecops
// Tool: appsec-devsecops/supply-chain-simulation/scripts/supply-chain-simulation_tool.py

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

module.exports.runtime = {
  handler: async function ({ input }) {
    try {
      const repoPath = this.runtimeArgs?.USAP_REPO_PATH || process.env.USAP_REPO_PATH;
      if (!repoPath) {
        return JSON.stringify({
          error: 'USAP_REPO_PATH not configured. Set it in the skill settings panel.',
          skill: 'supply-chain-simulation'
        });
      }

      const toolPath = path.join(repoPath, 'appsec-devsecops/supply-chain-simulation/scripts/supply-chain-simulation_tool.py');

      if (!fs.existsSync(toolPath)) {
        return JSON.stringify({
          error: `Tool not found at ${toolPath}. Check USAP_REPO_PATH.`,
          skill: 'supply-chain-simulation'
        });
      }

      let result;
      const hasInput = input && input.trim() !== '' && input.trim() !== '{}';

      if (hasInput) {
        // Write input to temp file to prevent shell injection
        const tmpFile = path.join(require('os').tmpdir(), `usap_input_${Date.now()}.json`);
        try {
          // Validate JSON before writing
          JSON.parse(input);
          fs.writeFileSync(tmpFile, input, 'utf-8');
          result = execSync(
            `python3 "${toolPath}" --input "${tmpFile}" --output json`,
            { encoding: 'utf-8', timeout: 30000, cwd: repoPath }
          ).trim();
        } finally {
          if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
        }
      } else {
        result = execSync(
          `python3 "${toolPath}" --output json`,
          { encoding: 'utf-8', timeout: 30000, cwd: repoPath }
        ).trim();
      }

      return result || JSON.stringify({ status: 'completed', skill: 'supply-chain-simulation', output: 'no output' });
    } catch (e) {
      return JSON.stringify({
        error: e.message,
        skill: 'supply-chain-simulation',
        hint: 'Ensure Python 3 is available and USAP_REPO_PATH is correct.'
      });
    }
  }
};
