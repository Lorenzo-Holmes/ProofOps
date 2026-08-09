from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proofops.catalog import SKILLS  # noqa: E402


def render_markdown(skill) -> str:
    name = skill.id.replace("_", "-")
    inputs = "\n".join(f"- `{item}`" for item in skill.inputs)
    outputs = "\n".join(f"- `{item}`" for item in skill.outputs)
    tools = "\n".join(f"- `{item}`" for item in skill.dependent_tools)
    agents = ", ".join(f"`{item}`" for item in skill.agent_ids)
    return f'''---
name: {name}
description: {skill.purpose}
version: {skill.version}
---

# {skill.name}

## Purpose

{skill.purpose}

## Invocation conditions

{skill.invocation_conditions}

## Inputs

{inputs}

## Outputs

{outputs}

## Dependent tools

{tools}

## Failure handling

{skill.failure_handling}

## Security boundary

{skill.security_boundary}

## Reuse value

{skill.reuse_value}

## Assigned agents

{agents}

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
'''


def main() -> int:
    root = ROOT / "skills"
    root.mkdir(parents=True, exist_ok=True)
    index = []
    for skill in SKILLS:
        name = skill.id.replace("_", "-")
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text(render_markdown(skill), encoding="utf-8")
        contract = skill.to_dict()
        contract["name"] = name
        (directory / "contract.json").write_text(
            json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        index.append({"name": name, "version": skill.version, "path": f"skills/{name}"})
    (ROOT / "agentteams" / "skills-index.json").write_text(
        json.dumps({"skills": index}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Exported {len(index)} AgentTeams skill packages to {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
