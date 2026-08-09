# Security Model

## Implemented controls

- [KNOWN] Default server binding is `127.0.0.1`; it is not exposed to other hosts unless the operator changes `--host`.
- [KNOWN] Static file resolution decodes URL paths, rejects `..`, resolves canonical paths and verifies the result remains under `web/`.
- [KNOWN] JSON request bodies are capped at 1 MiB and must decode to an object.
- [KNOWN] Write-capable state transitions stop at `awaiting_approval`.
- [KNOWN] Remediation, execution and verification are different Agent identities.
- [KNOWN] Audit events form a recalculable SHA-256 forward chain.
- [KNOWN] JSON persistence uses atomic replacement.
- [KNOWN] Browser rendering uses `textContent` and DOM construction rather than injecting API text as HTML.
- [KNOWN] Responses set `nosniff`, frame denial and no-referrer headers.

## Agent permissions

| Role | Read evidence | Propose change | Execute | Verify | Approve |
|---|---:|---:|---:|---:|---:|
| Commander | yes | no | no | no | no |
| Evidence | yes | no | no | no | no |
| Diagnosis | yes | no | no | no | no |
| Remediation | yes | yes | no | no | no |
| Execution | required context only | no | yes | no | no |
| Verification | baseline and candidate | no | no | yes | no |
| Human | visible | review | authorize | observe | yes |

## Deployment requirements

- [FRAME] When binding to `0.0.0.0`, place ProofOps behind an authenticated HTTPS gateway; the local MVP does not bundle Internet-facing authentication.
- [FRAME] Configure AgentTeams/Higress `allowedConsumers` or equivalent MCP tool allowlists per Worker; prompt instructions are not a permission system.
- [FRAME] Keep provider keys and repository credentials in the gateway, never in Worker manifests or Skill packages.
- [FRAME] Replace `HOST`, `PORT` and `MODEL_NAME` placeholders before applying the AgentTeams resources.
- [FRAME] Real deployment adapters must use short-lived credentials, explicit idempotency keys, scoped rollback points and environment allowlists.

## Residual work

- [FRAME] Add gateway authentication tests and per-Worker tool scopes before any shared-network deployment.
- [FRAME] Export audit traces to an OpenTelemetry collector and sign release artifacts.
- [FRAME] Add dependency and container image scanning when third-party runtime dependencies are introduced.
