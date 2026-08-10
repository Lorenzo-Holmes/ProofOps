(function proofOpsStaticDemoAdapter() {
  "use strict";

  const host = window.location.hostname.toLowerCase();
  const query = new URLSearchParams(window.location.search);
  const enabled =
    window.location.protocol === "file:" ||
    host === "github.io" ||
    host.endsWith(".github.io") ||
    query.get("demo") === "1";

  const STORAGE_KEY = "proofops.static-demo.v1";
  const STORE_VERSION = 1;
  const originalFetch = window.fetch.bind(window);

  if (!enabled) {
    window.ProofOpsDemoApi = Object.freeze({ enabled: false, active: false });
    return;
  }

  const SCENARIOS = [
    {
      id: "coupon-null-regression",
      name: "优惠券空值发布回归",
      service: "checkout-api",
      severity: "SEV-1",
      summary: "新版本在无优惠券订单路径产生HTTP 500并抬高结算失败率。",
      trigger: "checkout_error_rate > 8% for 5m",
      root_cause: "提交 7f3a2c1 将可选 coupon 对象改为非空访问。",
      candidate_hypotheses: ["数据库连接池耗尽", "支付依赖超时", "优惠券空值代码回归"],
      correlated_change: "checkout-api@7f3a2c1",
      remediation: "恢复空值分支并增加无优惠券回归测试。",
      rollback_plan: "回退至 checkout-api@2.8.4 并恢复上一配置快照。",
      verification_outcome: "pass",
      evidence_fixture: [
        {
          source: "prometheus",
          kind: "metric",
          summary: "结算错误率由0.7%升至12.4%",
          value: { before: 0.7, after: 12.4, unit: "%" },
        },
        {
          source: "otel",
          kind: "trace",
          summary: "NullReference集中于CouponResolver",
          value: { span: "CouponResolver.apply", errors: 186 },
        },
        {
          source: "git",
          kind: "change",
          summary: "异常开始前9分钟完成版本发布",
          value: { commit: "7f3a2c1", version: "2.8.5" },
        },
      ],
      baseline: { error_rate: 1.0, p95_ms: 420.0 },
      candidate_metrics: { error_rate: 0.6, p95_ms: 398.0 },
      risk_score: 42,
    },
    {
      id: "inventory-timeout-cascade",
      name: "库存超时级联与错误修复",
      service: "inventory-api",
      severity: "SEV-1",
      summary: "库存依赖超时造成请求堆积，候选补丁降低超时却引入库存误判。",
      trigger: "inventory_p95 > 1800ms and queue_depth > 500",
      root_cause: "下游批量查询缺少并发上限，峰值流量触发连接竞争。",
      candidate_hypotheses: ["缓存击穿", "数据库锁竞争", "批量查询并发失控"],
      correlated_change: "inventory-api@91bd033",
      remediation: "候选补丁直接缩短超时；沙箱验证将发现库存误判回归。",
      rollback_plan: "恢复 inventory-api@4.3.1 并启用旧版并发限制。",
      verification_outcome: "fail",
      evidence_fixture: [
        {
          source: "prometheus",
          kind: "metric",
          summary: "队列深度峰值达到742",
          value: { queue_depth: 742 },
        },
        {
          source: "otel",
          kind: "trace",
          summary: "BatchInventoryQuery占据91%关键路径",
          value: { span: "BatchInventoryQuery", share: 91 },
        },
        {
          source: "git",
          kind: "change",
          summary: "并发批量功能在当前版本启用",
          value: { commit: "91bd033", version: "4.3.2" },
        },
      ],
      baseline: { error_rate: 1.0, p95_ms: 900.0, inventory_accuracy: 99.9 },
      candidate_metrics: { error_rate: 0.8, p95_ms: 610.0, inventory_accuracy: 94.2 },
      risk_score: 68,
    },
  ];

  const AGENTS = [
    {
      id: "incident-commander",
      name: "指挥 Agent",
      role: "Orchestrator",
      purpose: "分解事件任务、推进状态机并维护人机协作边界。",
      capabilities: ["task_decomposition", "state_tracking", "approval_coordination"],
      security_boundary: "不得直接修改运行环境或绕过人工审批。",
      color: "#ff6b35",
    },
    {
      id: "evidence-agent",
      name: "证据 Agent",
      role: "Evidence Collector",
      purpose: "汇总告警、日志、Trace与变更记录并形成证据包。",
      capabilities: ["telemetry_query", "change_correlation", "evidence_normalization"],
      security_boundary: "仅拥有只读数据访问权限，不产生修复结论。",
      color: "#f2c14e",
    },
    {
      id: "diagnosis-agent",
      name: "诊断 Agent",
      role: "Hypothesis Tester",
      purpose: "提出竞争性根因假设并通过诊断实验寻找支持和反证。",
      capabilities: ["hypothesis_generation", "counter_evidence", "root_cause_ranking"],
      security_boundary: "诊断命令只能在隔离环境运行，不得写入生产数据。",
      color: "#5bc0eb",
    },
    {
      id: "remediation-agent",
      name: "修复 Agent",
      role: "Remediation Planner",
      purpose: "生成最小修复、影响评估和对应回滚计划。",
      capabilities: ["minimal_patch", "risk_scoring", "rollback_planning"],
      security_boundary: "只生成计划和补丁，不持有部署权限。",
      color: "#9bc53d",
    },
    {
      id: "execution-agent",
      name: "执行 Agent",
      role: "Controlled Executor",
      purpose: "在获得审批后执行沙箱、灰度和回滚操作。",
      capabilities: ["sandbox_execution", "canary_deployment", "rollback"],
      security_boundary: "必须验证短期审批令牌；所有写操作要求幂等键。",
      color: "#e55934",
    },
    {
      id: "verification-agent",
      name: "验证 Agent",
      role: "Independent Verifier",
      purpose: "独立执行回归测试、SLO检查和恢复验收。",
      capabilities: ["regression_testing", "slo_validation", "audit_verification"],
      security_boundary: "不得接受修复 Agent 的自证结果，不持有补丁修改权限。",
      color: "#b388eb",
    },
  ];

  const SKILLS = [
    {
      id: "incident_intake",
      name: "事件接入",
      version: "1.0.0",
      purpose: "标准化告警或工单并创建事件。",
      inputs: ["scenario_id", "trigger"],
      outputs: ["incident", "trace_id"],
      invocation_conditions: "收到有效事件输入时。",
      dependent_tools: ["event_bus"],
      failure_handling: "拒绝缺少服务或严重级别的输入并记录原因。",
      security_boundary: "仅创建内部事件，不调用写操作。",
      reuse_value: "可复用于告警、工单和发布事件。",
      agent_ids: ["incident-commander"],
    },
    {
      id: "collect_evidence",
      name: "证据采集",
      version: "1.0.0",
      purpose: "采集并标准化多源运行证据。",
      inputs: ["incident_id", "time_window", "service"],
      outputs: ["evidence_bundle"],
      invocation_conditions: "事件进入分诊阶段时。",
      dependent_tools: ["monitoring", "telemetry"],
      failure_handling: "数据源不可用时保留缺口，禁止伪造缺失数据。",
      security_boundary: "只读；结果需标记来源和采集时间。",
      reuse_value: "可复用于任何可观测服务。",
      agent_ids: ["evidence-agent"],
    },
    {
      id: "correlate_change",
      name: "变更关联",
      version: "1.0.0",
      purpose: "将异常时间窗与发布及配置变更关联。",
      inputs: ["evidence_bundle", "deployment_history"],
      outputs: ["candidate_changes"],
      invocation_conditions: "证据包达到最低完整度时。",
      dependent_tools: ["repository", "deployment"],
      failure_handling: "无相关变更时返回空集并扩大调查范围。",
      security_boundary: "代码仓库与发布记录均为只读。",
      reuse_value: "可迁移到不同Git及CI系统。",
      agent_ids: ["evidence-agent"],
    },
    {
      id: "test_hypothesis",
      name: "假设检验",
      version: "1.0.0",
      purpose: "运行可重复诊断并排序根因。",
      inputs: ["candidate_hypotheses", "evidence_bundle"],
      outputs: ["ranked_root_causes", "counter_evidence"],
      invocation_conditions: "至少存在两个候选假设时。",
      dependent_tools: ["diagnostic_runner"],
      failure_handling: "诊断失败时保留不确定度并请求补充证据。",
      security_boundary: "命令只能在隔离、只读环境运行。",
      reuse_value: "适用于软件、配置与依赖故障。",
      agent_ids: ["diagnosis-agent"],
    },
    {
      id: "plan_remediation",
      name: "修复规划",
      version: "1.0.0",
      purpose: "生成最小变更及回滚计划。",
      inputs: ["verified_root_cause", "risk_policy"],
      outputs: ["patch", "risk_score", "rollback_plan"],
      invocation_conditions: "根因置信度满足策略阈值时。",
      dependent_tools: ["repository"],
      failure_handling: "证据不足或风险过高时停止并升级给人工。",
      security_boundary: "无部署凭据；必须同时输出回滚计划。",
      reuse_value: "可复用于代码、配置和发布修复。",
      agent_ids: ["remediation-agent"],
    },
    {
      id: "apply_in_sandbox",
      name: "沙箱执行",
      version: "1.0.0",
      purpose: "在隔离环境应用补丁并运行测试。",
      inputs: ["patch", "approval_token", "idempotency_key"],
      outputs: ["build_result", "test_result"],
      invocation_conditions: "审批通过且令牌有效时。",
      dependent_tools: ["ci", "sandbox"],
      failure_handling: "超时或失败时清理工作区并阻止灰度。",
      security_boundary: "禁止直连生产；令牌短期有效且单次使用。",
      reuse_value: "适用于多种CI与容器平台。",
      agent_ids: ["execution-agent"],
    },
    {
      id: "verify_recovery",
      name: "恢复验证",
      version: "1.0.0",
      purpose: "使用独立基线验证功能和SLO。",
      inputs: ["baseline", "candidate_metrics", "regression_suite"],
      outputs: ["verdict", "verification_report"],
      invocation_conditions: "沙箱或灰度执行结束后。",
      dependent_tools: ["monitoring", "ci"],
      failure_handling: "任一强制断言失败即拒绝验收并触发回滚。",
      security_boundary: "只读验证，不接受执行方覆盖判定。",
      reuse_value: "可用于任何定义了验收契约的服务。",
      agent_ids: ["verification-agent"],
    },
    {
      id: "execute_rollback",
      name: "受控回滚",
      version: "1.0.0",
      purpose: "恢复到已验证的部署点并二次检查。",
      inputs: ["deployment_id", "rollback_point", "approval_token"],
      outputs: ["rollback_result"],
      invocation_conditions: "验证失败且存在有效回滚点时。",
      dependent_tools: ["deployment", "monitoring"],
      failure_handling: "重复调用保持幂等；失败时立即升级人工。",
      security_boundary: "仅允许回滚当前事件关联的部署。",
      reuse_value: "适用于支持版本化发布的平台。",
      agent_ids: ["execution-agent", "verification-agent"],
    },
  ];

  const TERMINAL_STATUSES = new Set(["resolved", "rolled_back", "rejected"]);
  let volatileStore = { version: STORE_VERSION, incidents: [] };

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function isStoredIncident(value) {
    return Boolean(
      value &&
        typeof value === "object" &&
        typeof value.id === "string" &&
        typeof value.status === "string" &&
        typeof value.scenario_name === "string" &&
        typeof value.service === "string" &&
        typeof value.severity === "string" &&
        typeof value.summary === "string" &&
        typeof value.trace_id === "string" &&
        value.context &&
        typeof value.context === "object" &&
        Array.isArray(value.events) &&
        value.events.every(
          (event) =>
            event &&
            typeof event === "object" &&
            Number.isInteger(event.sequence) &&
            typeof event.previous_hash === "string" &&
            typeof event.event_hash === "string" &&
            Array.isArray(event.evidence) &&
            event.metrics &&
            typeof event.metrics === "object",
        ),
    );
  }

  function readStore() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return clone(volatileStore);
      const parsed = JSON.parse(raw);
      if (
        parsed?.version !== STORE_VERSION ||
        !Array.isArray(parsed.incidents) ||
        !parsed.incidents.every(isStoredIncident)
      ) {
        return clone(volatileStore);
      }
      volatileStore = parsed;
    } catch (_error) {
      // Some browsers restrict localStorage for file:// pages; the in-memory
      // store keeps that demo session functional without widening interception.
    }
    return clone(volatileStore);
  }

  function writeStore(store) {
    volatileStore = clone(store);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(volatileStore));
    } catch (_error) {
      // The volatile copy is the intentional fallback for restricted contexts.
    }
  }

  function resetStore() {
    volatileStore = { version: STORE_VERSION, incidents: [] };
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch (_error) {
      // Keep the volatile store reset even when persistent storage is blocked.
    }
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function randomHex(length) {
    const byteLength = Math.ceil(length / 2);
    const bytes = new Uint8Array(byteLength);
    if (window.crypto?.getRandomValues) {
      window.crypto.getRandomValues(bytes);
    } else {
      for (let index = 0; index < byteLength; index += 1) {
        bytes[index] = Math.floor(Math.random() * 256);
      }
    }
    return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("").slice(0, length);
  }

  function stableStringify(value) {
    if (value === null || typeof value !== "object") return JSON.stringify(value);
    if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
    const entries = Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`);
    return `{${entries.join(",")}}`;
  }

  function rotateRight(value, amount) {
    return (value >>> amount) | (value << (32 - amount));
  }

  function sha256Fallback(input) {
    const bytes = new TextEncoder().encode(input);
    const bitLength = bytes.length * 8;
    const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
    const padded = new Uint8Array(paddedLength);
    padded.set(bytes);
    padded[bytes.length] = 0x80;
    const view = new DataView(padded.buffer);
    const high = Math.floor(bitLength / 0x100000000);
    const low = bitLength >>> 0;
    view.setUint32(paddedLength - 8, high, false);
    view.setUint32(paddedLength - 4, low, false);

    const constants = [
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ];
    const hash = [
      0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    ];
    const words = new Uint32Array(64);

    for (let offset = 0; offset < paddedLength; offset += 64) {
      for (let index = 0; index < 16; index += 1) words[index] = view.getUint32(offset + index * 4, false);
      for (let index = 16; index < 64; index += 1) {
        const x = words[index - 15];
        const y = words[index - 2];
        const sigma0 = rotateRight(x, 7) ^ rotateRight(x, 18) ^ (x >>> 3);
        const sigma1 = rotateRight(y, 17) ^ rotateRight(y, 19) ^ (y >>> 10);
        words[index] = (words[index - 16] + sigma0 + words[index - 7] + sigma1) >>> 0;
      }

      let [a, b, c, d, e, f, g, h] = hash;
      for (let index = 0; index < 64; index += 1) {
        const sum1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
        const choice = (e & f) ^ (~e & g);
        const temp1 = (h + sum1 + choice + constants[index] + words[index]) >>> 0;
        const sum0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
        const majority = (a & b) ^ (a & c) ^ (b & c);
        const temp2 = (sum0 + majority) >>> 0;
        h = g;
        g = f;
        f = e;
        e = (d + temp1) >>> 0;
        d = c;
        c = b;
        b = a;
        a = (temp1 + temp2) >>> 0;
      }
      hash[0] = (hash[0] + a) >>> 0;
      hash[1] = (hash[1] + b) >>> 0;
      hash[2] = (hash[2] + c) >>> 0;
      hash[3] = (hash[3] + d) >>> 0;
      hash[4] = (hash[4] + e) >>> 0;
      hash[5] = (hash[5] + f) >>> 0;
      hash[6] = (hash[6] + g) >>> 0;
      hash[7] = (hash[7] + h) >>> 0;
    }

    return hash.map((value) => value.toString(16).padStart(8, "0")).join("");
  }

  async function sha256Hex(input) {
    if (window.crypto?.subtle) {
      try {
        const digest = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
        return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
      } catch (_error) {
        // Fall through to the local SHA-256 implementation for file:// contexts.
      }
    }
    return sha256Fallback(input);
  }

  function makeEvidence(source, kind, summary, value) {
    return {
      id: `evd-${randomHex(10)}`,
      source,
      kind,
      summary,
      value: clone(value),
      collected_at: nowIso(),
    };
  }

  async function appendEvent(incident, agentId, skillId, action, summary, outcome, result) {
    const event = {
      id: `evt-${randomHex(12)}`,
      sequence: incident.events.length + 1,
      timestamp: nowIso(),
      trace_id: incident.trace_id,
      span_id: `spn-${randomHex(16)}`,
      agent_id: agentId,
      skill_id: skillId,
      action,
      summary,
      outcome,
      evidence: clone(result.evidence || []),
      metrics: clone(result.metrics || {}),
      previous_hash: incident.events.at(-1)?.event_hash || "GENESIS",
    };
    event.event_hash = await sha256Hex(stableStringify(event));
    incident.events.push(event);
    incident.updated_at = event.timestamp;
    return event;
  }

  function findScenario(scenarioId) {
    return SCENARIOS.find((scenario) => scenario.id === scenarioId) || null;
  }

  function findIncident(store, incidentId) {
    return store.incidents.find((incident) => incident.id === incidentId) || null;
  }

  async function createIncident(scenarioId) {
    const scenario = findScenario(scenarioId);
    if (!scenario) throw apiError(404, "scenario_not_found", `未知故障样本：${scenarioId}`);
    const createdAt = nowIso();
    const incident = {
      id: `inc-${randomHex(10)}`,
      scenario_id: scenario.id,
      scenario_name: scenario.name,
      service: scenario.service,
      severity: scenario.severity,
      summary: scenario.summary,
      status: "detected",
      created_at: createdAt,
      updated_at: createdAt,
      trace_id: `trc-${randomHex(32)}`,
      context: {
        trigger: scenario.trigger,
        candidate_hypotheses: clone(scenario.candidate_hypotheses),
        risk_score: scenario.risk_score,
        target_outcome: scenario.verification_outcome === "pass" ? "resolved" : "rolled_back",
      },
      approval: null,
      events: [],
    };
    await appendEvent(
      incident,
      "incident-commander",
      "incident_intake",
      "incident.detected",
      `已接收${scenario.service}事件：${scenario.trigger}`,
      "completed",
      { evidence: [], metrics: { severity: scenario.severity } },
    );
    return incident;
  }

  function evidenceResult(scenario, operation) {
    if (operation === "evidence.collect") {
      const evidence = scenario.evidence_fixture.map((item) =>
        makeEvidence(item.source, item.kind, item.summary, item.value),
      );
      return {
        summary: `已从${evidence.length}个来源建立标准化证据包。`,
        evidence,
        metrics: { sources: evidence.length, evidence_completeness_percent: 100.0 },
      };
    }
    if (operation === "change.correlate") {
      return {
        summary: "已将异常时间窗与发布记录关联。",
        evidence: [
          makeEvidence(
            "repository",
            "correlation",
            `高相关变更：${scenario.correlated_change}`,
            { change: scenario.correlated_change, correlation: 0.93 },
          ),
        ],
        metrics: { candidates: 1 },
      };
    }
    if (operation === "hypothesis.test") {
      return {
        summary: "竞争性假设检验完成，已保留支持证据与反证。",
        evidence: [
          makeEvidence("diagnostic-runner", "hypothesis-test", scenario.root_cause, {
            tested: clone(scenario.candidate_hypotheses),
            selected: scenario.candidate_hypotheses.at(-1),
            confidence: 0.88,
            counter_evidence_count: scenario.candidate_hypotheses.length - 1,
          }),
        ],
        metrics: { hypotheses_tested: scenario.candidate_hypotheses.length },
      };
    }
    if (operation === "remediation.plan") {
      return {
        summary: "最小修复与对应回滚计划已生成，等待人工审批。",
        evidence: [
          makeEvidence("remediation-planner", "change-plan", scenario.remediation, {
            patch: scenario.remediation,
            rollback: scenario.rollback_plan,
            risk_score: scenario.risk_score,
          }),
        ],
        metrics: { risk_score: scenario.risk_score },
      };
    }
    if (operation === "sandbox.apply") {
      return {
        summary: "沙箱执行完成，进入独立恢复验证。",
        evidence: [
          makeEvidence("ci-sandbox", "test-run", "补丁已在隔离环境构建并执行回归套件。", {
            tests_total: 48,
            tests_passed: 48,
            candidate: scenario.correlated_change,
          }),
        ],
        metrics: { tests_total: 48, tests_passed: 48 },
      };
    }
    if (operation === "recovery.verify") {
      const passed = scenario.verification_outcome === "pass";
      const summary = passed ? "恢复指标与业务断言均通过。" : "业务准确率断言失败，拒绝验收。";
      return {
        summary,
        evidence: [
          makeEvidence("independent-verifier", "verification", summary, {
            baseline: clone(scenario.baseline),
            candidate: clone(scenario.candidate_metrics),
            passed,
          }),
        ],
        metrics: { passed, checks: Object.keys(scenario.baseline).length },
      };
    }
    if (operation === "deployment.rollback") {
      return {
        summary: "已回滚至验证版本并通过二次健康检查。",
        evidence: [
          makeEvidence("deployment", "rollback", scenario.rollback_plan, {
            idempotent: true,
            health_check: "passed",
          }),
        ],
        metrics: { rollback_verified: true },
      };
    }
    throw apiError(404, "operation_not_found", `未知工具操作：${operation}`);
  }

  async function advanceIncident(incident) {
    const scenario = findScenario(incident.scenario_id);
    if (!scenario) throw apiError(404, "scenario_not_found", `未知故障样本：${incident.scenario_id}`);

    if (incident.status === "detected") {
      incident.status = "triaging";
      const result = evidenceResult(scenario, "evidence.collect");
      await appendEvent(incident, "evidence-agent", "collect_evidence", "evidence.collected", result.summary, "completed", result);
    } else if (incident.status === "triaging") {
      incident.status = "diagnosing";
      const result = evidenceResult(scenario, "change.correlate");
      await appendEvent(incident, "evidence-agent", "correlate_change", "change.correlated", result.summary, "completed", result);
    } else if (incident.status === "diagnosing") {
      incident.status = "planning";
      const result = evidenceResult(scenario, "hypothesis.test");
      await appendEvent(incident, "diagnosis-agent", "test_hypothesis", "diagnosis.verified", result.summary, "completed", result);
    } else if (incident.status === "planning") {
      incident.status = "awaiting_approval";
      const result = evidenceResult(scenario, "remediation.plan");
      await appendEvent(incident, "remediation-agent", "plan_remediation", "remediation.proposed", result.summary, "completed", result);
    } else if (incident.status === "awaiting_approval") {
      throw apiError(409, "approval_required", "高风险写操作需要人工批准。");
    } else if (incident.status === "executing") {
      incident.status = "verifying";
      const result = evidenceResult(scenario, "sandbox.apply");
      await appendEvent(incident, "execution-agent", "apply_in_sandbox", "sandbox.executed", result.summary, "completed", result);
    } else if (incident.status === "verifying") {
      const result = evidenceResult(scenario, "recovery.verify");
      const passed = Boolean(result.metrics.passed);
      incident.status = passed ? "resolved" : "rolling_back";
      await appendEvent(
        incident,
        "verification-agent",
        "verify_recovery",
        passed ? "verification.accepted" : "verification.failed",
        result.summary,
        passed ? "completed" : "failed",
        result,
      );
    } else if (incident.status === "rolling_back") {
      incident.status = "rolled_back";
      const result = evidenceResult(scenario, "deployment.rollback");
      await appendEvent(incident, "execution-agent", "execute_rollback", "deployment.rollback", result.summary, "completed", result);
    } else {
      throw apiError(409, "invalid_transition", `终态事件不能继续推进：${incident.status}`);
    }
    incident.updated_at = nowIso();
    return incident;
  }

  async function approveIncident(incident, actor, reason) {
    const normalizedActor = String(actor || "").trim();
    if (!normalizedActor) throw apiError(400, "invalid_input", "审批人不能为空。");
    if (incident.status !== "awaiting_approval") {
      throw apiError(409, "invalid_transition", "只有等待审批的事件可以批准。");
    }
    const decidedAt = nowIso();
    incident.approval = {
      actor: normalizedActor,
      decision: "approved",
      reason: String(reason ?? "approved for demo"),
      decided_at: decidedAt,
    };
    incident.status = "executing";
    await appendEvent(
      incident,
      "incident-commander",
      "plan_remediation",
      "approval.granted",
      `${normalizedActor}已批准受控沙箱执行。`,
      "completed",
      { evidence: [], metrics: { human_approved: true } },
    );
    incident.updated_at = nowIso();
    return incident;
  }

  async function rejectIncident(incident, actor, reason) {
    const normalizedActor = String(actor || "").trim();
    const normalizedReason = String(reason || "").trim();
    if (!normalizedActor || !normalizedReason) {
      throw apiError(400, "invalid_input", "驳回需要审批人和原因。");
    }
    if (incident.status !== "awaiting_approval") {
      throw apiError(409, "invalid_transition", "只有等待审批的事件可以驳回。");
    }
    const decidedAt = nowIso();
    incident.approval = {
      actor: normalizedActor,
      decision: "rejected",
      reason: normalizedReason,
      decided_at: decidedAt,
    };
    incident.status = "rejected";
    await appendEvent(
      incident,
      "incident-commander",
      "plan_remediation",
      "approval.rejected",
      `${normalizedActor}驳回执行：${normalizedReason}`,
      "completed",
      { evidence: [], metrics: { human_approved: false } },
    );
    incident.updated_at = nowIso();
    return incident;
  }

  async function verifyAudit(events) {
    if (!Array.isArray(events)) return false;
    let previous = "GENESIS";
    for (let index = 0; index < events.length; index += 1) {
      const event = events[index];
      if (
        !event ||
        event.sequence !== index + 1 ||
        event.previous_hash !== previous ||
        !/^[a-f0-9]{64}$/.test(event.event_hash)
      ) {
        return false;
      }
      const { event_hash: eventHash, ...payload } = event;
      if ((await sha256Hex(stableStringify(payload))) !== eventHash) return false;
      previous = event.event_hash;
    }
    return true;
  }

  async function metricsFor(store) {
    const events = store.incidents.flatMap((incident) => incident.events);
    const auditResults = await Promise.all(store.incidents.map((incident) => verifyAudit(incident.events)));
    const valid = auditResults.filter(Boolean).length;
    const traced = events.filter((event) => event.trace_id && event.span_id).length;
    const total = store.incidents.length;
    return {
      incidents_total: total,
      active_total: store.incidents.filter((incident) => !TERMINAL_STATUSES.has(incident.status)).length,
      resolved_total: store.incidents.filter((incident) => incident.status === "resolved").length,
      rolled_back_total: store.incidents.filter((incident) => incident.status === "rolled_back").length,
      rejected_total: store.incidents.filter((incident) => incident.status === "rejected").length,
      human_approvals_total: store.incidents.filter((incident) => incident.approval?.decision === "approved").length,
      audit_integrity_percent: total ? Math.round((valid / total) * 1000) / 10 : 100.0,
      trace_coverage_percent: events.length ? Math.round((traced / events.length) * 1000) / 10 : 100.0,
      events_total: events.length,
    };
  }

  function apiError(status, code, message) {
    const error = new Error(message);
    error.apiStatus = status;
    error.apiCode = code;
    return error;
  }

  function jsonResponse(status, payload) {
    return new Response(JSON.stringify(payload), {
      status,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-ProofOps-Demo": "static-adapter",
      },
    });
  }

  async function parseBody(input, options) {
    let body = options?.body;
    if (body === undefined && input instanceof Request && input.method !== "GET" && input.method !== "HEAD") {
      body = await input.clone().text();
    }
    if (body === undefined || body === null || body === "") return {};
    if (typeof body === "string") {
      try {
        const parsed = JSON.parse(body);
        if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
          throw new Error("JSON请求体必须是对象。");
        }
        return parsed;
      } catch (error) {
        throw apiError(400, "invalid_json", error.message);
      }
    }
    if (body instanceof URLSearchParams) return Object.fromEntries(body.entries());
    throw apiError(400, "invalid_json", "静态演示仅接受JSON对象请求体。");
  }

  async function dispatch(method, path, body) {
    if (method === "GET" && path === "/api/health") {
      return jsonResponse(200, { status: "ok", service: "proofops-static-demo", version: "1.0.0" });
    }
    if (method === "GET" && path === "/api/scenarios") return jsonResponse(200, { items: clone(SCENARIOS) });
    if (method === "GET" && path === "/api/agents") return jsonResponse(200, { items: clone(AGENTS) });
    if (method === "GET" && path === "/api/skills") return jsonResponse(200, { items: clone(SKILLS) });

    const store = readStore();
    if (method === "GET" && path === "/api/metrics") return jsonResponse(200, await metricsFor(store));
    if (path === "/api/incidents") {
      if (method === "GET") return jsonResponse(200, { items: clone(store.incidents) });
      if (method === "POST") {
        if (typeof body.scenario_id !== "string" || !body.scenario_id) {
          throw apiError(400, "invalid_input", "scenario_id不能为空。");
        }
        const incident = await createIncident(body.scenario_id);
        store.incidents.unshift(incident);
        writeStore(store);
        return jsonResponse(201, { incident: clone(incident) });
      }
    }

    const match = path.match(/^\/api\/incidents\/([^/]+)(?:\/(advance|approve|reject|audit))?$/);
    if (!match) throw apiError(404, "route_not_found", `未找到路由：${method} ${path}`);
    const incident = findIncident(store, decodeURIComponent(match[1]));
    if (!incident) throw apiError(404, "incident_not_found", `事件不存在：${decodeURIComponent(match[1])}`);
    const operation = match[2];

    if (!operation && method === "GET") return jsonResponse(200, { incident: clone(incident) });
    if (operation === "audit" && method === "GET") {
      return jsonResponse(200, {
        incident_id: incident.id,
        valid: await verifyAudit(incident.events),
        events: clone(incident.events),
      });
    }
    if (method !== "POST" || !["advance", "approve", "reject"].includes(operation)) {
      throw apiError(404, "route_not_found", `未找到路由：${method} ${path}`);
    }

    if (operation === "advance") await advanceIncident(incident);
    if (operation === "approve") await approveIncident(incident, body.actor, body.reason);
    if (operation === "reject") await rejectIncident(incident, body.actor, body.reason);
    writeStore(store);
    return jsonResponse(200, { incident: clone(incident) });
  }

  window.fetch = async function proofOpsDemoFetch(input, options = {}) {
    const requestUrl = input instanceof Request ? input.url : String(input);
    let url;
    try {
      url = new URL(requestUrl, window.location.href);
    } catch (_error) {
      return originalFetch(input, options);
    }
    let path = url.pathname.replace(/\/+$/, "") || "/";
    // An absolute `/api/...` URL resolves to `/C:/api/...` under file:// on
    // Windows. Normalize only that file-demo form; hosted pages stay untouched.
    if (window.location.protocol === "file:") {
      const apiOffset = path.indexOf("/api/");
      if (apiOffset >= 0) path = path.slice(apiOffset);
    }
    if (!path.startsWith("/api/")) return originalFetch(input, options);

    const method = String(options.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
    try {
      const body = await parseBody(input, options);
      return await dispatch(method, path, body);
    } catch (error) {
      const status = Number(error.apiStatus) || 500;
      const code = error.apiCode || "demo_adapter_error";
      return jsonResponse(status, { error: { code, message: error.message || "静态演示请求失败。" } });
    }
  };

  window.ProofOpsDemoApi = Object.freeze({
    enabled: true,
    active: true,
    storageKey: STORAGE_KEY,
    fetch: window.fetch,
    handle: (path, options) => window.fetch(path, options),
    reset: resetStore,
    snapshot: () => readStore(),
  });
})();
