---
name: collect-evidence
description: 采集并标准化多源运行证据。
version: 1.0.0
---

# 证据采集

## Purpose

采集并标准化多源运行证据。

## Invocation conditions

事件进入分诊阶段时。

## Inputs

- `incident_id`
- `time_window`
- `service`

## Outputs

- `evidence_bundle`

## Dependent tools

- `monitoring`
- `telemetry`

## Failure handling

数据源不可用时保留缺口，禁止伪造缺失数据。

## Security boundary

只读；结果需标记来源和采集时间。

## Reuse value

可复用于任何可观测服务。

## Assigned agents

`evidence-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
