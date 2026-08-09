---
name: incident-intake
description: 标准化告警或工单并创建事件。
version: 1.0.0
---

# 事件接入

## Purpose

标准化告警或工单并创建事件。

## Invocation conditions

收到有效事件输入时。

## Inputs

- `scenario_id`
- `trigger`

## Outputs

- `incident`
- `trace_id`

## Dependent tools

- `event_bus`

## Failure handling

拒绝缺少服务或严重级别的输入并记录原因。

## Security boundary

仅创建内部事件，不调用写操作。

## Reuse value

可复用于告警、工单和发布事件。

## Assigned agents

`incident-commander`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
