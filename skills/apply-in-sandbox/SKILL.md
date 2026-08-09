---
name: apply-in-sandbox
description: 在隔离环境应用补丁并运行测试。
version: 1.0.0
---

# 沙箱执行

## Purpose

在隔离环境应用补丁并运行测试。

## Invocation conditions

审批通过且令牌有效时。

## Inputs

- `patch`
- `approval_token`
- `idempotency_key`

## Outputs

- `build_result`
- `test_result`

## Dependent tools

- `ci`
- `sandbox`

## Failure handling

超时或失败时清理工作区并阻止灰度。

## Security boundary

禁止直连生产；令牌短期有效且单次使用。

## Reuse value

适用于多种CI与容器平台。

## Assigned agents

`execution-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
