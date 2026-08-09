# Architecture

## 1. System boundary

[KNOWN] ProofOps runs as one local Python process. The HTTP layer exposes static files, a REST API and an MCP JSON-RPC endpoint. The domain layer is independent from transport, so tests call it without a network server.

[FRAME] External monitoring, repository, CI and deployment systems sit behind `FixtureToolGateway`. Replacing this class with MCP/HTTP adapters does not change the incident state machine or audit model.

## 2. State machine

```text
detected → triaging → diagnosing → planning → awaiting_approval
                                                     │
                                  reject ─────────────┤
                                                     ▼
                                                executing
                                                     ▼
                                                verifying
                                                  ╱     ╲
                                             pass       fail
                                              ▼           ▼
                                           resolved  rolling_back
                                                           ▼
                                                     rolled_back
```

[KNOWN] `awaiting_approval` is a blocking state. `advance()` raises `ApprovalRequired`; only `approve()` or `reject()` can leave it.

[KNOWN] Verification belongs to a separate Agent and separate Skill. A failed verdict cannot be converted to success by the execution or remediation role; it enters the rollback branch.

## 3. AgentTeams mapping

| ProofOps role | AgentTeams resource | Collaboration responsibility |
|---|---|---|
| Incident Commander | Team Leader Worker | decomposition, state tracking, human escalation |
| Evidence Agent | Worker | read-only telemetry and change evidence |
| Diagnosis Agent | Worker | competing hypotheses and counter-evidence |
| Remediation Agent | Worker | minimum patch and rollback plan |
| Execution Agent | Worker | approved sandbox/canary action and rollback |
| Verification Agent | Worker | independent business and SLO acceptance |
| Demo Judge | Human | visible approval or rejection |

[KNOWN] The resource manifest uses `agentteams.io/v1beta1`, `workerMembers`, `peerMentions` and MCP server declarations aligned with AgentTeams v1.2.x documentation.

## 4. Skill layer

[KNOWN] `catalog.py` is the source of truth for eight Skill contracts. `scripts/export_skills.py` generates a `SKILL.md` and `contract.json` package for every Skill. Catalog validation tests require inputs, outputs, invocation conditions, dependent tools, failure handling, security boundaries, reuse value and assigned agents.

## 5. Evidence and audit

[KNOWN] Every `AuditEvent` contains sequence, UTC timestamp, trace/span identifiers, Agent, Skill, action, outcome, evidence, metrics, previous hash and current hash.

[KNOWN] The hash is SHA-256 over canonical UTF-8 JSON with sorted keys. The first event points to `GENESIS`; every later event points to the previous event hash. `verify_audit()` recalculates every hash and checks the sequence.

## 6. Persistence

[KNOWN] `JsonIncidentStore` writes each event aggregate to a temporary file and atomically replaces the final JSON file. Tests verify round-trip deserialization and absence of leftover temporary files.

## 7. Interface contracts

[KNOWN] REST is used by the browser console. MCP exposes the same engine to AgentTeams or another MCP client. Tool execution failures return `isError=true`; unknown tools return a JSON-RPC protocol error.

[KNOWN] MCP supports current stateless discovery (`server/discover`, protocol `2026-07-28`) and legacy initialization for `2025-11-25`, `2025-06-18` and `2025-03-26` clients.
