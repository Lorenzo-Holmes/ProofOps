---
name: plan-remediation
description: 生成最小变更及回滚计划。
version: 1.0.0
---

# 修复规划

## Purpose

生成最小变更及回滚计划。

## Invocation conditions

根因置信度满足策略阈值时。

## Inputs

- `verified_root_cause`
- `risk_policy`

## Outputs

- `patch`
- `risk_score`
- `rollback_plan`

## Dependent tools

- `repository`

## Failure handling

证据不足或风险过高时停止并升级给人工。

## Security boundary

无部署凭据；必须同时输出回滚计划。

## Reuse value

可复用于代码、配置和发布修复。

## Assigned agents

`remediation-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
