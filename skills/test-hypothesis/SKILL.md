---
name: test-hypothesis
description: 运行可重复诊断并排序根因。
version: 1.0.0
---

# 假设检验

## Purpose

运行可重复诊断并排序根因。

## Invocation conditions

至少存在两个候选假设时。

## Inputs

- `candidate_hypotheses`
- `evidence_bundle`

## Outputs

- `ranked_root_causes`
- `counter_evidence`

## Dependent tools

- `diagnostic_runner`

## Failure handling

诊断失败时保留不确定度并请求补充证据。

## Security boundary

命令只能在隔离、只读环境运行。

## Reuse value

适用于软件、配置与依赖故障。

## Assigned agents

`diagnosis-agent`

## Execution contract

1. Validate every required input before calling a tool.
2. Return structured output plus evidence identifiers.
3. Preserve `incident_id`, `trace_id`, event sequence and failure status.
4. Stop when the security boundary or invocation condition is not satisfied.
