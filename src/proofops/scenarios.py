from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    service: str
    severity: str
    summary: str
    trigger: str
    root_cause: str
    candidate_hypotheses: tuple[str, ...]
    correlated_change: str
    remediation: str
    rollback_plan: str
    verification_outcome: str
    evidence_fixture: tuple[dict[str, Any], ...]
    baseline: dict[str, float]
    candidate_metrics: dict[str, float]
    risk_score: int

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidate_hypotheses"] = list(self.candidate_hypotheses)
        payload["evidence_fixture"] = list(self.evidence_fixture)
        return payload


SCENARIOS: dict[str, Scenario] = {
    "coupon-null-regression": Scenario(
        id="coupon-null-regression",
        name="优惠券空值发布回归",
        service="checkout-api",
        severity="SEV-1",
        summary="新版本在无优惠券订单路径产生HTTP 500并抬高结算失败率。",
        trigger="checkout_error_rate > 8% for 5m",
        root_cause="提交 7f3a2c1 将可选 coupon 对象改为非空访问。",
        candidate_hypotheses=("数据库连接池耗尽", "支付依赖超时", "优惠券空值代码回归"),
        correlated_change="checkout-api@7f3a2c1",
        remediation="恢复空值分支并增加无优惠券回归测试。",
        rollback_plan="回退至 checkout-api@2.8.4 并恢复上一配置快照。",
        verification_outcome="pass",
        evidence_fixture=(
            {"source": "prometheus", "kind": "metric", "summary": "结算错误率由0.7%升至12.4%", "value": {"before": 0.7, "after": 12.4, "unit": "%"}},
            {"source": "otel", "kind": "trace", "summary": "NullReference集中于CouponResolver", "value": {"span": "CouponResolver.apply", "errors": 186}},
            {"source": "git", "kind": "change", "summary": "异常开始前9分钟完成版本发布", "value": {"commit": "7f3a2c1", "version": "2.8.5"}},
        ),
        baseline={"error_rate": 1.0, "p95_ms": 420.0},
        candidate_metrics={"error_rate": 0.6, "p95_ms": 398.0},
        risk_score=42,
    ),
    "inventory-timeout-cascade": Scenario(
        id="inventory-timeout-cascade",
        name="库存超时级联与错误修复",
        service="inventory-api",
        severity="SEV-1",
        summary="库存依赖超时造成请求堆积，候选补丁降低超时却引入库存误判。",
        trigger="inventory_p95 > 1800ms and queue_depth > 500",
        root_cause="下游批量查询缺少并发上限，峰值流量触发连接竞争。",
        candidate_hypotheses=("缓存击穿", "数据库锁竞争", "批量查询并发失控"),
        correlated_change="inventory-api@91bd033",
        remediation="候选补丁直接缩短超时；沙箱验证将发现库存误判回归。",
        rollback_plan="恢复 inventory-api@4.3.1 并启用旧版并发限制。",
        verification_outcome="fail",
        evidence_fixture=(
            {"source": "prometheus", "kind": "metric", "summary": "队列深度峰值达到742", "value": {"queue_depth": 742}},
            {"source": "otel", "kind": "trace", "summary": "BatchInventoryQuery占据91%关键路径", "value": {"span": "BatchInventoryQuery", "share": 91}},
            {"source": "git", "kind": "change", "summary": "并发批量功能在当前版本启用", "value": {"commit": "91bd033", "version": "4.3.2"}},
        ),
        baseline={"error_rate": 1.0, "p95_ms": 900.0, "inventory_accuracy": 99.9},
        candidate_metrics={"error_rate": 0.8, "p95_ms": 610.0, "inventory_accuracy": 94.2},
        risk_score=68,
    ),
}


def list_scenarios() -> list[dict[str, Any]]:
    return [scenario.to_dict() for scenario in SCENARIOS.values()]

