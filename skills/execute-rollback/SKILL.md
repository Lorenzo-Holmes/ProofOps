---
name: execute-rollback
description: 恢复到已验证的部署点并二次检查。
version: 1.0.0
---

# 受控回滚

## Purpose

恢复到已验证的部署点并二次检查。

## Invocation conditions

验证失败且存在有效回滚点时。

## Inputs

- `deployment_id`
- `rollback_point`
- `approval_token`

## Outputs

- `rollback_result`

## Dependent tools

- `deployment`
- `monitoring`

## Failure handling

重复调用保持幂等；失败时立即升级人工。

## Security boundary

仅允许回滚当前事件关联的部署。

## Reuse value

适用于支持版本化发布的平台。

## Assigned agents

`execution-agent`, `verification-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
