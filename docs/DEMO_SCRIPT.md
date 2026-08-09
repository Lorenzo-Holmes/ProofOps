# Demo Script

## A. Successful recovery branch

1. [FRAME] Open `http://127.0.0.1:8787/` and select “优惠券空值发布回归”.
2. [FRAME] State the problem: a release raised checkout errors from the fixture baseline to 12.4%.
3. [FRAME] Create the incident and press “自动运行”.
4. [FRAME] During evidence collection, point to Prometheus, OTel and Git evidence items and the shared Trace ID.
5. [FRAME] During diagnosis, emphasize three competing hypotheses and retained counter-evidence.
6. [FRAME] At the approval dialog, explain that no write-capable Agent can cross the gate alone; enter the judge identity and approve.
7. [FRAME] Show sandbox tests, independent verification and final `resolved` status.
8. [FRAME] Click the last timeline event and show the SHA-256 chain, Skill contract and audit completeness.

## B. Failed verification and rollback branch

1. [FRAME] Select “库存超时级联与错误修复” and start automatic execution.
2. [FRAME] Approve the local sandbox action after showing the risk score and rollback plan.
3. [FRAME] Explain that latency improves but inventory accuracy drops from the baseline; the independent verifier rejects the candidate.
4. [FRAME] Show `rolling_back` followed by `rolled_back` and the verified rollback evidence.
5. [FRAME] Contrast the result with a single Agent that might accept its own technically successful patch.

## C. Judge questions

- [FRAME] **Why multiple Agents?** Role separation prevents the patch generator from being its own verifier and keeps read/write permissions separable.
- [FRAME] **What is actually open source?** Engine, state machine, eight Skill packages, MCP adapter, AgentTeams resources, fixtures, UI and tests.
- [FRAME] **What is simulated?** Monitoring, repository, CI and deployment connectors; their interfaces and evidence contracts are real, their default outputs are deterministic fixtures.
- [FRAME] **How is rollback proven?** Verification failure creates an auditable state transition; rollback is idempotent and followed by a second health check.
- [FRAME] **How is AgentTeams used?** The manifest maps six Workers into a Team with a Team Leader, Matrix-visible human and MCP server contract.

## D. Timing

- [FRAME] Context and pain: 40 seconds.
- [FRAME] Successful branch: 120 seconds.
- [FRAME] Rollback branch: 90 seconds.
- [FRAME] Architecture, evidence and open-source assets: 60 seconds.
- [COMPUTED] Total target: 310 seconds, or 5 minutes 10 seconds.
