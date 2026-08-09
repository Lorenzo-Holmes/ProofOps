---
name: verify-recovery
description: 使用独立基线验证功能和SLO。
version: 1.0.0
---

# 恢复验证

## Purpose

使用独立基线验证功能和SLO。

## Invocation conditions

沙箱或灰度执行结束后。

## Inputs

- `baseline`
- `candidate_metrics`
- `regression_suite`

## Outputs

- `verdict`
- `verification_report`

## Dependent tools

- `monitoring`
- `ci`

## Failure handling

任一强制断言失败即拒绝验收并触发回滚。

## Security boundary

只读验证，不接受执行方覆盖判定。

## Reuse value

可用于任何定义了验收契约的服务。

## Assigned agents

`verification-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
