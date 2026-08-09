# ProofOps

> 证据驱动的多 Agent 企业故障闭环系统

[KNOWN] ProofOps 是面向 GOAI 2026「Agent Infra 新智基座」赛道开发的本地可运行 MVP。它用确定性故障样本展示事件接入、证据采集、竞争性根因诊断、修复规划、人工审批、受控执行、独立验证、失败回滚和哈希链审计。

[KNOWN] 当前版本不依赖第三方 Python 包；Python 3.11+ 即可运行。浏览器界面、REST API、MCP JSON-RPC 端点和持久化存储由同一进程提供。

## 已实现能力

- [KNOWN] 六个不同职能 Agent 的 Identity、能力和安全边界。
- [KNOWN] 两条完整演示分支：成功恢复、验证失败后回滚。
- [KNOWN] 写操作前的人工审批状态；审批和驳回均进入审计链。
- [KNOWN] 八个版本化 Skill 契约及 AgentTeams 分发目录。
- [KNOWN] 每个事件使用 SHA-256 前向哈希链记录 Trace、Agent、Skill、证据和指标。
- [KNOWN] JSON 文件原子持久化、REST API、响应式指挥台和零依赖 HTTP 服务。
- [KNOWN] MCP `tools/list` / `tools/call`、2026-07-28 `server/discover` 以及旧版 `initialize` 兼容。
- [KNOWN] AgentTeams v1.2.x `Manager`、`Worker`、`Team`、`Human` CRD 示例。

## 30秒启动

```powershell
cd ProofOps
python app.py
```

[KNOWN] 默认入口：

- 指挥台：`http://127.0.0.1:8787/`
- 健康检查：`http://127.0.0.1:8787/api/health`
- MCP端点：`http://127.0.0.1:8787/mcp`

[KNOWN] 也可使用脚本：

```powershell
.\scripts\run.ps1
```

## 演示流程

1. [KNOWN] 在左侧选择“优惠券空值发布回归”或“库存超时级联与错误修复”。
2. [KNOWN] 点击“创建事件”，再点击“自动运行”。
3. [KNOWN] 系统依次生成证据、变更关联、假设检验和修复计划。
4. [KNOWN] 到达 `awaiting_approval` 后流程强制暂停并显示人工审批对话框。
5. [KNOWN] 批准后进入沙箱执行和独立验证。
6. [KNOWN] 优惠券样本进入 `resolved`；库存样本因业务准确率回归进入 `rolling_back`，最终为 `rolled_back`。
7. [KNOWN] 点击任一时间线事件可查看证据来源、Skill契约和哈希摘要。

## 系统结构

```text
Browser Console
      │ REST
      ▼
ProofOps HTTP Server ────── /mcp JSON-RPC ────── AgentTeams / MCP Client
      │
      ├── Domain Engine + State Machine
      ├── Agent / Skill Catalog
      ├── Fixture Tool Gateway
      ├── Independent Verifier
      └── JSON Incident Store + Audit Hash Chain
```

[KNOWN] 目录说明：

```text
agentteams/              AgentTeams CRD清单与Skill索引
mcp-servers/proofops/    MCP服务元数据
skills/                  8个可分发Skill包
src/proofops/            领域引擎、API、MCP、存储和服务器
web/                     比赛展示指挥台
tests/                   领域、API、MCP、HTTP、安全与前端契约测试
docs/                    架构、演示、安全和提交材料
scripts/                 启动、测试及Skill导出脚本
work/data/               本地运行数据；默认不纳入版本库
```

## REST API

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/api/scenarios` | 列出故障样本 |
| `POST` | `/api/incidents` | 创建事件 |
| `GET` | `/api/incidents` | 读取事件队列 |
| `GET` | `/api/incidents/{id}` | 读取事件详情 |
| `POST` | `/api/incidents/{id}/advance` | 推进一步 |
| `POST` | `/api/incidents/{id}/approve` | 记录人工批准 |
| `POST` | `/api/incidents/{id}/reject` | 驳回计划 |
| `GET` | `/api/incidents/{id}/audit` | 校验并读取审计链 |
| `GET` | `/api/metrics` | 读取聚合指标 |

## MCP调用示例

```powershell
$body = @{
  jsonrpc = "2.0"
  id = 1
  method = "tools/list"
  params = @{}
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8787/mcp `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

[KNOWN] 写入型工具带有 `readOnlyHint=false` 和 `destructiveHint=true`；MCP宿主应在调用前显示人工确认。ProofOps自身仍在 `awaiting_approval` 状态阻断未批准执行。

## AgentTeams接入

[KNOWN] `agentteams/proofops-team.yaml` 使用 `agentteams.io/v1beta1`，包含1个Manager、6个Worker、1个Team和1个Human资源。

1. [FRAME] 安装并启动 AgentTeams v1.2.x。
2. [FRAME] 将清单中的 `MODEL_NAME`、`HOST`、`PORT` 替换为本地配置；容器访问宿主机时，`HOST`不能填写容器自身的`127.0.0.1`。
3. [FRAME] 将 `skills/` 中的包交付到对应Worker，或发布到团队使用的Skill注册表。
4. [FRAME] 用AgentTeams CLI应用清单：

```powershell
agt apply -f agentteams/proofops-team.yaml
```

5. [FRAME] 在Gateway按Worker配置MCP工具白名单；证据、诊断和修复Agent不应获得审批或执行权限。

## 测试

```powershell
cd ProofOps
$env:PYTHONPATH = "src"
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m unittest discover -s tests -v
node --check web/app.js
```

[KNOWN] `scripts/test.ps1`封装了同一组检查。

## 真实与模拟边界

- [KNOWN] 已真实实现：状态机、审批、持久化、审计哈希、API、MCP协议适配、前端交互和自动测试。
- [FRAME] 当前模拟：Prometheus、OpenTelemetry、Git、CI及Deployment调用返回可重复的内置证据。
- [FRAME] 下一阶段：以真实MCP适配器替换Fixture Tool Gateway，并增加OpenTelemetry导出、基准故障集和AgentTeams现场运行录像。

## 开源

[KNOWN] 本项目使用 Apache-2.0 许可证，见 `LICENSE`。第三方运行依赖为零；AgentTeams属于可选外部集成，不随本仓库分发。

