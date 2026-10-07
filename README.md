# 科技产业研究原型

> **文档入口**：工程宪章与依赖铁律见 [`AGENTS.md`](AGENTS.md)；13 道确定性门禁的逐门权威评分卡见 [`GATE_SCORECARD.md`](GATE_SCORECARD.md)；演进变更见 AGENTS.md §6 变更记录；外围扩展任务归档见 [`TASK_ARCHIVE.md`](TASK_ARCHIVE.md)。

项目包含研究技能、关键词路由、研报草稿及审计脚本。当前 RAG 检索执行链已具备关键词/现象词/可选语义向量召回的检索基础设施，并配套决策卡与门禁审计。

## 运行

在项目根目录运行，Python 3.12，当前脚本仅使用标准库：

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/deterministic_judge.py --benchmark-dir reports/nvidia_benchmark
python scripts/evidence_auditor_harness.py --benchmark-dir reports/nvidia_benchmark
python scripts/eval_rag.py                       # RAG 确定性评测（Hit/MRR/饥饿率）
python scripts/batch_ingest_all.py --limit 5     # 全量批处理（Canary；四安全规范）
```

非 PASS 返回退出码 1。默认审稿配置中的 inherit 没有可执行模型后端，返回 NOT_RUN，不会认证任何断言。配置 `config/pipeline_config.json` 的 `tiers.tier_2_evidence_auditor.model_config.custom_override` 后，可加 `--use-override` 调用已配置的 OpenAI 兼容端点。

启用外部审稿会向该端点发送断言、认识论类型及独立抓取的来源文本。来源 URL 必须是操作者信任的公共 HTTP(S) 地址；此原型不应作为接收任意外部 URL 的网络服务部署。

## 验证语义

- 来源门禁：仅接受本次 harness 抓取的快照和重新计算的 SHA-256，不信任 evidence.jsonl 自填的 HTTP 状态或哈希。
- 语义门禁：解析审稿模型 JSON，并校验证据摘录确实存在于抓取文本。FULL 才能通过；模型判断仍可能错误。
- 公式门禁：要求参数卡提供 `calculation: {"expression": "a*b", "inputs": {"a": 2, "b": 3}}` 和 `base_value: 6`。只验证算术，不证明参数来源或量纲正确。禁止 eval；不支持的表达式不放行。
- UNVERIFIED / NOT_RUN / ERROR 均不能产生整体 PASS。当前未实现独立锁参见证与验证集访问隔离，因此整体审计不会认证通过。修复没有通过伪造这些能力来使样例变绿。
- 评分卡记录具体 `report.md` 的绝对路径与内容哈希，不适用于其他报告或修改后的版本；尚无全文断言覆盖率检查。
- 快照保存在 `source_snapshots/`，审稿结果保存在 `verification_results.json`。后者用于人工追溯，新进程不自动信任磁盘上的历史审稿结果。
- 抓取暂支持最多 2 MB 的 HTML/纯文本；PDF、超长文本和受限页面需要另建提取器，当前会明确失败。

## 历史数据及剩余限制

`reports/*benchmark` 中的历史文件含演示性质记录、手填时间戳和未验证引用。保留用于追溯；新评分卡覆盖旧 PASS。两个 scaffold 脚本现在仅输出到 `fixtures/generated/`，不会覆盖正式研报。

其他历史 `build_*` / `update_*` / `patch_*` 脚本属于旧版本迁移工具，不是可信审计入口，请勿用其生成的预设结论覆盖评分卡。

出生类型、正交性、因果关系、估值措辞等旧门禁仍主要是结构或关键词检查，规则匹配通过会单独记录 structural_check=PASS，但门禁保持 UNVERIFIED，不能解释为事实认证。独立外部取证、完整模型复算、报告断言覆盖和运行隔离仍需继续建设。
