---
name: correlate-change
description: 将异常时间窗与发布及配置变更关联。
version: 1.0.0
---

# 变更关联

## Purpose

将异常时间窗与发布及配置变更关联。

## Invocation conditions

证据包达到最低完整度时。

## Inputs

- `evidence_bundle`
- `deployment_history`

## Outputs

- `candidate_changes`

## Dependent tools

- `repository`
- `deployment`

## Failure handling

无相关变更时返回空集并扩大调查范围。

## Security boundary

代码仓库与发布记录均为只读。

## Reuse value

可迁移到不同Git及CI系统。

## Assigned agents

`evidence-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
