# scripts/archive/ — 历史迁移脚本归档区

> 按 2026-10-04 目录整洁化规程，以下 `build_* / patch_* / update_* / fix_* / sync_*` 脚本为 v3.x 时期的**一次性数据迁移/补丁工具**，已从 `scripts/` 根目录移入本归档区，不再参与门禁流水线与测试发现。

## 归档清单（11 个）

| 脚本 | 用途（从代码注释归纳） |
| --- | --- |
| `build_v3_4_benchmark.py` | v3.4 评测数据生成器 |
| `build_v3_5_artifacts.py` | v3.5 产物补全（评分卡/证据链）生成器 |
| `patch_judge_v3_4.py` | v3.4 裁判逻辑补丁 |
| `patch_judge_v3_5.py` | v3.5 裁判逻辑补丁（门禁/引擎参数） |
| `fix_cards_derivation_steps.py` | 修复参数卡推导步骤字段 |
| `sync_assumptions_v3_5.py` | 同步假设 JSON 到 v3.5 schema |
| `update_config_v3_5.py` | 配置迁移到 v3.5 |
| `update_report_v3_4.py` | 报告迁移到 v3.4 |
| `update_report_v3_5.py` | 报告迁移到 v3.5 |
| `update_report_v3_5_enforcement.py` | v3.5 强制门禁字段迁移 |
| `update_thesis_v3_5.py` | 论点 JSON 迁移到 v3.5 |

## 原则（请共同遵守）

1. **不归档**：运行时核心引擎（`deterministic_judge.py`、`evidence_auditor_harness.py`、`problem_router.py`、`strict_gates.py`、`verification.py`）与 fixture 生成器（`scaffold_*`）必须留在 `scripts/` 根，它们是审计流水线的可信入口。
2. **勿回迁**：除非拿到明确的业务理由，不要把这些一次性的旧迁移脚本再挪回 `scripts/` 根——它们会让 `unittest discover` 和代码审查误以为仍是活跃工具。
3. 归档区内脚本仅供参考、考据，不再维护。