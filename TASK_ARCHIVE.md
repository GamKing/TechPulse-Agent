# 外围扩展任务归档（P2 · 已归档入库）

> 本文件归档两个**外围扩展任务**。它们被定位为"架构演进 / 外围扩展"层级（P2），
> 已记录完整规格但不在此仓库实现——因为两者均涉足独立微服务 / 第三方采集能力，
> 不属于本仓库"纯 Python 标准库 + Fail-Closed 确定性核心"（AGENTS.md 依赖铁律）的范畴。
> 归档目的是：职责隔离、防止外围能力污染核心验证库；后续实现可参考本规格独立落地。
> 状态：**已归档（ARCHIVED）** · 本仓库仅保留规格，不 hold 实现。

---

## TASK-EXT-SCRAPER-01 · 外围独立防反爬无头采集微服务

### 目标
为 Tier 2 证据采集提供一个**独立于主仓库**的无头浏览器采集微服务，用真实渲染对抗反爬
（Cloudflare / JS 动态渲染 / 登录墙），把抓到的页面作为离线快照落盘，交给主系统
`import_offline_snapshot` / `fetch_source_offline` 走 Air-gapped 证据注入。

### 为何独立 / 为何归档
- 主系统坚持纯标准库 + Fail-Closed 确定性（AGENTS.md 依赖铁律）。无头采集（Playwright/Puppeteer）
  依赖重（浏览器内核、重型 pip 包），会破坏 Zero-pip 底线。
- 证据"是否被采集到"是可失败的外部动作，不应进入确定性门禁链；门禁只认**离线快照的 SHA-256**。
  因此采集微服务与外网请求被隔离在独立进程，主系统只消费其落盘产物。

### 规格
| 维度 | 定义 |
|---|---|
| 语言/依赖 | Node.js / Playwright(或 Python + playwright)；**独立 venv**，不进主仓库 requirements |
| 协议 | HTTP 微服务；POST `/fetch` {url, max_redirects} → {snapshot_bin, content_type, status, sha256} |
| 输出 | 快照写入远端共同目录 `source_snapshots/manual/<sha256>.bin`（与主系统 Air-gapped 协议对齐） |
| 反爬策略 | 真实浏览器指纹、随机UA、等待JS渲染、可选代理池；失败返回 429/403 标记（不伪造成功） |
| 安全 | 只接受调用方白名单 URL（防 SSRF）；快照永不入库 Git（走主系统 manifest） |
| 验收 | 能采 ag-news/SEC/Gartner 等反爬目标；产出 SHA-256 可被主系统 `fetch_source_offline` 命中 |

### 与主系统衔接
```
[采集微服务(独立)] --落盘 sha256.bin--> source_snapshots/manual/
                                           ↓ import_offline_snapshot (主系统，纯stdlib)
                                      manifest.json --fetch_source_offline--> Gate1 哈希比对
```

---

## TASK-ARCH-LLM-WIKI-01 · 产业拓扑与多跳 Wiki 索引层建设

### 目标
在主系统 RAG 之上，建设**多跳（multi-hop）产业拓扑 Wiki 索引**——不只做单切片关键词召回，
而是建立"企业 → 产业链环节 → 控制点 → 上游/下游 → 竞争格局"的结构化一跳/多跳推理索引，
支撑 Gate 10（因果距离）与 Gate 12（知行合一）的推理链校验。

### 为何归档
- 当前系统已具备关键词/现象词/微事实/语义向量召回（`retrieve_axioms`），但**多跳 Figeroa 推理
  与产业拓扑图谱**是需要"结构化知识建模"的演进项，与"确定性门禁核心"阶段性解耦，先归档规格。
- 构建拓扑需成熟的实体-关系抽取（LLM/规则），会引入非确定性依赖，不宜混入纯代码核心。

### 规格
| 维度 | 定义 |
|---|---|
| 数据层 | `rag/research/topology_graph.json`：节点(firm/segment/control_point) + 边(depends/competes/supplies) |
| 检索 | 一层: 现有 `retrieve_axioms`；二层: 命中实体后沿边做 1-2 跳拓扑召回，注入 `retrieved_axioms` 扩展字段 |
| 因果 | 每条检索链标注 hop_distance；Gate 10 用 hop_distance 强化因果距离惩罚（远跳不得声称强支持） |
| 校验 | `test_topology_multi_hop.py`：从"英伟达→CoWoS→TSMC"断言 2 跳可达；`eval_rag.py` 增 multi-hop 考题 |
| 验收 | 多跳查询（"英伟达供应链里谁掌握封装环节"）能返回带 hop 标注的拓扑证据链，且因果距离门禁正确奖惩 |

### 与主系统衔接
```
retrieve_axioms (单跳关键词)  +  topology_graph (多跳图谱)
        └─────────────┬─────────────────┘
               retrieved_axioms 扩展 [topic_path, hop_distance]
                          ↓
              Gate 10 因果距离(用 hop) / Gate 12 知行合一
```

---

## 归档备注
- 本文件只作**规格 + 职责隔离**记录，不包含实现（避免外围依赖污染核心）。
- 如需启动实现，须先在 AGENTS.md 申请对应依赖豁免（如 playwright / 图谱库），再独立开发。
- 相关主线资产: `GATE_SCORECARD.md`（13 门禁）、`scripts/fetch_source_offline`（离线证据）、`scripts/eval_rag.py`（评测）。