from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    id: str
    name: str
    role: str
    purpose: str
    capabilities: tuple[str, ...]
    security_boundary: str
    color: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        return payload


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    id: str
    name: str
    version: str
    purpose: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    invocation_conditions: str
    dependent_tools: tuple[str, ...]
    failure_handling: str
    security_boundary: str
    reuse_value: str
    agent_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        payload = asdict(self)
        for key in ("inputs", "outputs", "dependent_tools", "agent_ids"):
            payload[key] = list(payload[key])
        return payload


AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "incident-commander",
        "指挥 Agent",
        "Orchestrator",
        "分解事件任务、推进状态机并维护人机协作边界。",
        ("task_decomposition", "state_tracking", "approval_coordination"),
        "不得直接修改运行环境或绕过人工审批。",
        "#ff6b35",
    ),
    AgentDefinition(
        "evidence-agent",
        "证据 Agent",
        "Evidence Collector",
        "汇总告警、日志、Trace与变更记录并形成证据包。",
        ("telemetry_query", "change_correlation", "evidence_normalization"),
        "仅拥有只读数据访问权限，不产生修复结论。",
        "#f2c14e",
    ),
    AgentDefinition(
        "diagnosis-agent",
        "诊断 Agent",
        "Hypothesis Tester",
        "提出竞争性根因假设并通过诊断实验寻找支持和反证。",
        ("hypothesis_generation", "counter_evidence", "root_cause_ranking"),
        "诊断命令只能在隔离环境运行，不得写入生产数据。",
        "#5bc0eb",
    ),
    AgentDefinition(
        "remediation-agent",
        "修复 Agent",
        "Remediation Planner",
        "生成最小修复、影响评估和对应回滚计划。",
        ("minimal_patch", "risk_scoring", "rollback_planning"),
        "只生成计划和补丁，不持有部署权限。",
        "#9bc53d",
    ),
    AgentDefinition(
        "execution-agent",
        "执行 Agent",
        "Controlled Executor",
        "在获得审批后执行沙箱、灰度和回滚操作。",
        ("sandbox_execution", "canary_deployment", "rollback"),
        "必须验证短期审批令牌；所有写操作要求幂等键。",
        "#e55934",
    ),
    AgentDefinition(
        "verification-agent",
        "验证 Agent",
        "Independent Verifier",
        "独立执行回归测试、SLO检查和恢复验收。",
        ("regression_testing", "slo_validation", "audit_verification"),
        "不得接受修复 Agent 的自证结果，不持有补丁修改权限。",
        "#b388eb",
    ),
)


SKILLS: tuple[SkillDefinition, ...] = (
    SkillDefinition(
        "incident_intake", "事件接入", "1.0.0", "标准化告警或工单并创建事件。",
        ("scenario_id", "trigger"), ("incident", "trace_id"),
        "收到有效事件输入时。", ("event_bus",),
        "拒绝缺少服务或严重级别的输入并记录原因。",
        "仅创建内部事件，不调用写操作。", "可复用于告警、工单和发布事件。",
        ("incident-commander",),
    ),
    SkillDefinition(
        "collect_evidence", "证据采集", "1.0.0", "采集并标准化多源运行证据。",
        ("incident_id", "time_window", "service"), ("evidence_bundle",),
        "事件进入分诊阶段时。", ("monitoring", "telemetry"),
        "数据源不可用时保留缺口，禁止伪造缺失数据。",
        "只读；结果需标记来源和采集时间。", "可复用于任何可观测服务。",
        ("evidence-agent",),
    ),
    SkillDefinition(
        "correlate_change", "变更关联", "1.0.0", "将异常时间窗与发布及配置变更关联。",
        ("evidence_bundle", "deployment_history"), ("candidate_changes",),
        "证据包达到最低完整度时。", ("repository", "deployment"),
        "无相关变更时返回空集并扩大调查范围。",
        "代码仓库与发布记录均为只读。", "可迁移到不同Git及CI系统。",
        ("evidence-agent",),
    ),
    SkillDefinition(
        "test_hypothesis", "假设检验", "1.0.0", "运行可重复诊断并排序根因。",
        ("candidate_hypotheses", "evidence_bundle"), ("ranked_root_causes", "counter_evidence"),
        "至少存在两个候选假设时。", ("diagnostic_runner",),
        "诊断失败时保留不确定度并请求补充证据。",
        "命令只能在隔离、只读环境运行。", "适用于软件、配置与依赖故障。",
        ("diagnosis-agent",),
    ),
    SkillDefinition(
        "plan_remediation", "修复规划", "1.0.0", "生成最小变更及回滚计划。",
        ("verified_root_cause", "risk_policy"), ("patch", "risk_score", "rollback_plan"),
        "根因置信度满足策略阈值时。", ("repository",),
        "证据不足或风险过高时停止并升级给人工。",
        "无部署凭据；必须同时输出回滚计划。", "可复用于代码、配置和发布修复。",
        ("remediation-agent",),
    ),
    SkillDefinition(
        "apply_in_sandbox", "沙箱执行", "1.0.0", "在隔离环境应用补丁并运行测试。",
        ("patch", "approval_token", "idempotency_key"), ("build_result", "test_result"),
        "审批通过且令牌有效时。", ("ci", "sandbox"),
        "超时或失败时清理工作区并阻止灰度。",
        "禁止直连生产；令牌短期有效且单次使用。", "适用于多种CI与容器平台。",
        ("execution-agent",),
    ),
    SkillDefinition(
        "verify_recovery", "恢复验证", "1.0.0", "使用独立基线验证功能和SLO。",
        ("baseline", "candidate_metrics", "regression_suite"), ("verdict", "verification_report"),
        "沙箱或灰度执行结束后。", ("monitoring", "ci"),
        "任一强制断言失败即拒绝验收并触发回滚。",
        "只读验证，不接受执行方覆盖判定。", "可用于任何定义了验收契约的服务。",
        ("verification-agent",),
    ),
    SkillDefinition(
        "execute_rollback", "受控回滚", "1.0.0", "恢复到已验证的部署点并二次检查。",
        ("deployment_id", "rollback_point", "approval_token"), ("rollback_result",),
        "验证失败且存在有效回滚点时。", ("deployment", "monitoring"),
        "重复调用保持幂等；失败时立即升级人工。",
        "仅允许回滚当前事件关联的部署。", "适用于支持版本化发布的平台。",
        ("execution-agent", "verification-agent"),
    ),
)


def validate_catalog() -> list[str]:
    errors: list[str] = []
    agent_ids = {agent.id for agent in AGENTS}
    required_text = (
        "id", "name", "version", "purpose", "invocation_conditions",
        "failure_handling", "security_boundary", "reuse_value",
    )
    for skill in SKILLS:
        for field_name in required_text:
            if not getattr(skill, field_name):
                errors.append(f"{skill.id}.{field_name} is required")
        for field_name in ("inputs", "outputs", "dependent_tools", "agent_ids"):
            if not getattr(skill, field_name):
                errors.append(f"{skill.id}.{field_name} is required")
        unknown = set(skill.agent_ids) - agent_ids
        if unknown:
            errors.append(f"{skill.id}.agent_ids contains unknown agents: {sorted(unknown)}")
    return errors

