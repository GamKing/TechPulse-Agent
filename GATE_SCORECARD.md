# agent-rag 统一黄金评分卡 (GATE_SCORECARD · 自动生成)

> 本文件由 `scripts/generate_gate_scorecard.py` 自动生成于 `2026-10-05T04:47:24.643994+00:00`。
> 门禁清单来自 `deterministic_judge.execute_audit()` 实际执行（非手写），确保与代码同步。
> 基准: `reports/nvidia_benchmark` | 主题: `nvidia`

## 总判定: **PASS** (exit 0)

| 类别 | 通过 | 总数 |
| :--- | :--- | :--- |
| CRITICAL | 6 / 6 |
| HIGH | 7 / 7 |

## 门禁明细

| 门禁 | 优先级 | 状态 | 说明 |
| :--- | :---: | :---: | :--- |
| `GATE_SOURCE_EXISTENCE` | CRITICAL | PASS | 来源物理存在性：快照重算 SHA-256 与凭证一致 |
| `GATE_CLAIM_ENTAILMENT_TARGET_RESULT` | CRITICAL | PASS | 语义蕴含 × 目标漂移：独立审稿 FULL |
| `GATE_EPISTEMIC_BIRTH_CERTIFICATE` | CRITICAL | PASS | 认识论出生证：禁止二手估算冒充 FACT |
| `GATE_PARAMETER_PROVENANCE_RECALCULATION` | CRITICAL | PASS | 参数溯源 AST 重算（无大模型，纯代码） |
| `GATE_PARAMETER_ORTHOGONALITY_DUAL_MODEL` | CRITICAL | PASS | 双模型参数正交 + 诚实残差规则 |
| `GATE_PARAMETER_PREREGISTRATION_BLIND` | CRITICAL | PASS | 预登记盲审：参数先固化、哈希锁定、防事后挑拣 |
| `GATE_VALIDATION_LEAKAGE` | HIGH | PASS | 验证泄漏防火墙：holdout 隔离+独立审计+时序 |
| `GATE_ARTIFACT_ENFORCEMENT` | HIGH | PASS | 产物完整性：9 件必需产物俱在 |
| `GATE_GLOBAL_PRECISION_REGEX_AUDIT` | HIGH | PASS | 全局精度正则：认知标签齐全 + 无伪精度 |
| `GATE_CAUSAL_DISTANCE_PENALTY` | HIGH | PASS | 因果距离惩罚：远距离证据不得声称强支持 |
| `GATE_VALUATION_DECOUPLING` | HIGH | PASS | 估值脱钩：禁煽动词 + 三级脱钩 |
| `GATE_DECISION_CONSISTENCY` | HIGH | PASS | 知行合一：公理方向与研报结论方向一致 |
| `GATE_PARAMETER_UNIT_CONTRACT` | HIGH | PASS | 单位契约：参数卡声明 unit + AST 跨量纲检查 |

## Fail-Closed 语义

- **PASS**: 在物理数据/纯代码下被证明通过
- **FAIL**: 拒绝（数据伪造/缺失/篡改）
- **UNVERIFIED**: 证据不足——聚合中视为未过关，绝不当作通过

> 聚合规则: 任一 CRITICAL 非 PASS → FAIL；无 critical 失败但 HIGH 非 PASS → PARTIAL_PASS；全 PASS → PASS。
> 生成命令: `python scripts/generate_gate_scorecard.py --benchmark-dir {benchmark_dir}`
