#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 确定性评测矩阵 (self-built, pure stdlib, zero external libs)
Frontier Tech Industrial Analysis Engine

自建 RAG 评测——绝不引入 Ragas / TruLens / DeepEval（违背 Zero-pip 底线与 Fail-Closed 哲学：
Ragas 本质是 LLM-as-a-Judge 的模糊打分，与"防大模型自产自评"根基相悖）。
本脚本 100% 纯 Python 标准库，把 RAG 拆解为三个硬核确定性指标：

  1. 检索召回层 (Retrieval)      —— Hit@K / MRR（纯代码比对 chunk_id，无模型）
  2. 席位均衡度 (Quota Health)   —— 微观事实切片饥饿率（纯规则计数）
  3. 认识论承接 (Epistemic Carry)—— 方法论主题命中率（检索是否"搜对主题"）

评测数据集: tests/retrieval_golden_dataset.json
  每个 case: {query, expected_topic(可选，方法论canonical), expected_fact_ids(可选，微事实chunk_id)}
  ground-truth 用 chunk_id 精确比对（方法论切片 Dxxx_Cyyy，微事实用 fact_id）。

用法:
  python scripts/eval_rag.py
  python scripts/eval_rag.py --dataset tests/retrieval_golden_dataset.json --top-k 5

指标阈值(可配置):
  hit_rate >= 60%      (检索召回合格线)
  starvation_rate == 0 (微观事实饥饿必须为 0)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from problem_router import ProblemRouter

DEFAULT_DATASET = Path(__file__).resolve().parents[1] / "tests/retrieval_golden_dataset.json"


def load_dataset(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_rag_benchmark(dataset_path=DEFAULT_DATASET, top_k: int = 5,
                      hit_threshold: float = 60.0, mrr_threshold: float = 0.30):
    cases = load_dataset(dataset_path)
    total = len(cases)
    hits = 0
    mrr_sum = 0.0
    starvation_cases = 0
    topic_hits = 0
    router = ProblemRouter()

    print(f"=== RAG 确定性检索基准评测 (共 {total} 题, top_k={top_k}) ===")
    print(f"数据集: {dataset_path}\n")

    for idx, case in enumerate(cases, 1):
        q = case["query"]
        exp_topic = case.get("expected_topic")
        exp_facts = set(case.get("expected_fact_ids", []))
        # 执行路由 + 检索（top_k）
        decision = router.route(q)
        recalled = decision.get("retrieved_axioms", [])[:top_k]
        recalled_ids = [c.get("chunk_id", "") for c in recalled]
        recalled_epi = [c.get("epistemic_type", "") for c in recalled]

        # ---- 指标2：席位饥饿率（只对"期望微观事实"的查询生效）----
        # 纯方法论查询(佩蕾丝/兰切斯特等)本就不应招回事实切片，不算饥饿；
        # 只有期望事实的查询(有 expected_fact_ids)在 top_k 内事实切片过少才算饥饿。
        if exp_facts:
            fact_count = sum(1 for e in recalled_epi if e == "FACT")
            if fact_count < 2:
                starvation_cases += 1

        # ---- 指标1：Hit@K / MRR ----
        # 目标 = 预期主题的方法论切片(按主题) 或 显式预期 fact chunk_id
        target_hit = False
        best_rank = 0
        for rank, c in enumerate(recalled, 1):
            cid = c.get("chunk_id", "")
            topics = set(c.get("methodology_topics", []))
            # 主题命中：期望主题出现在该切片方法论主题中
            if exp_topic and exp_topic in topics:
                target_hit = True
                if not best_rank:
                    best_rank = rank
            # 事实命中：期望的 fact_id 精确匹配
            if exp_facts and cid in exp_facts:
                target_hit = True
                if not best_rank:
                    best_rank = rank
        if target_hit:
            hits += 1
            mrr_sum += 1.0 / best_rank
        # ---- 指标3：认识论承接（至少命中一个预期主题）----
        if exp_topic:
            hit_topic = any(exp_topic in set(c.get("methodology_topics", []))
                            for c in recalled)
            if hit_topic:
                topic_hits += 1

    hit_rate = (hits / total) * 100
    avg_mrr = mrr_sum / total
    starve_rate = (starvation_cases / total) * 100
    topic_rate = (topic_hits / max(total, 1)) * 100

    print(f"--- 结果 ---")
    print(f"Hit@{top_k} 召回率     : {hit_rate:.2f}%  (阈值 >= {hit_threshold}%)")
    print(f"MRR 平均倒数排名   : {avg_mrr:.4f}  (阈值 >= {mrr_threshold})")
    print(f"微观事实饥饿率     : {starve_rate:.2f}%  (目标 0.0%)")
    print(f"方法论主题承接率   : {topic_rate:.2f}%")

    # 门禁断言
    fail = []
    if hit_rate < hit_threshold:
        fail.append(f"Hit@{top_k} 低于阈值 {hit_threshold}%")
    if avg_mrr < mrr_threshold:
        fail.append(f"MRR 低于阈值 {mrr_threshold}")
    if starve_rate > 0:
        fail.append("微观事实饥饿率必须为 0%")

    if fail:
        print(f"\n[FAIL] RAG 检索未达标: {'; '.join(fail)}", file=sys.stderr)
        sys.exit(1)
    print("\n[PASS] RAG 检索性能符合决策引擎标准！")
    sys.exit(0)


def main():
    ap = argparse.ArgumentParser(description="RAG 确定性评测（纯标准库，无三方依赖）")
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--hit-threshold", type=float, default=60.0)
    ap.add_argument("--mrr-threshold", type=float, default=0.30)
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    run_rag_benchmark(Path(args.dataset), args.top_k, args.hit_threshold, args.mrr_threshold)


if __name__ == "__main__":
    main()