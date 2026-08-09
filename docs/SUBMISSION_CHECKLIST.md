# GOAI Submission Checklist

## Preliminary submission

- [KNOWN] Project name and sub-500-character description: drafted in `docs/PROJECT_INTRO.md`.
- [KNOWN] Scenario value, Agent identities, task decomposition and state machine: `README.md` and `docs/ARCHITECTURE.md`.
- [KNOWN] Skill list, contracts, failure handling and security boundaries: `skills/` and `src/proofops/catalog.py`.
- [KNOWN] Exception, approval and rollback branches: engine tests and `docs/DEMO_SCRIPT.md`.
- [KNOWN] Open-source plan and license: `LICENSE`, `README.md` and this repository layout.

## Semi-final package

- [KNOWN] Executable entry point: `app.py` and `scripts/run.ps1`.
- [KNOWN] Dependency instructions: Python 3.11+, zero runtime packages.
- [KNOWN] Sample inputs and outputs: two scenarios in `src/proofops/scenarios.py`.
- [KNOWN] Runnable browser Demo: `web/`.
- [KNOWN] AgentTeams code material: `agentteams/proofops-team.yaml`.
- [KNOWN] MCP contract: `/mcp`, `mcp-servers/proofops/server.json` and MCP tests.
- [KNOWN] Logs/Trace/Metrics evidence: incident audit events and `/api/metrics`.
- [KNOWN] Approval, rollback and audit: automated engine and API tests.
- [FRAME] Remaining: real AgentTeams deployment recording, demo video, benchmark table and final PPT/PDF.

## Final review gate

- [FRAME] Run `scripts/test.ps1` on a clean machine.
- [FRAME] Run both demo branches and retain JSON audit exports.
- [FRAME] Replace every target metric in the deck with measured results.
- [FRAME] Verify third-party notices, screenshots, links and repository access.
- [FRAME] Prepare an offline video and local deployment fallback for the venue network.
