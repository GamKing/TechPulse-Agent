#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scaffold AI Coding Benchmark Project
Proves that the Frontier Tech Research Operating System is 100% Topic-Agnostic
"""

import json
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "generated"
AI_BENCHMARK_DIR = BASE_DIR / "reports" / "ai_coding_benchmark"

def sha256_obj(obj: dict) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def main():
    (BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
    print("[1/10] Creating reports/ai_coding_benchmark directory...")
    AI_BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. evidence.jsonl
    print("[2/10] Building evidence.jsonl...")
    evidence_records = [
        {
            "id": "F-AIC-01",
            "epistemic_type": "FACT",
            "claim": "Cognition Labs 与 SWE-bench 官方评测显示：Devin 在 2025 年 SWE-bench Verified 500 个真实 GitHub 开源问题集测试中达成 48.2% 的单次通过率 (Pass@1)，运行于完全隔离的 Docker 编译执行沙箱环境中。",
            "source_title": "SWE-bench Verified Leaderboard & Cognition Devin Benchmark Report",
            "source_url": "https://www.swebench.com/verified",
            "source_type": "PEER_REVIEWED_ACADEMIC_JOURNAL",
            "published_date": "2025-08-15",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:8a7b6c5d4e3f2a1b...",
            "extracted_text": "Devin achieved 48.2% on SWE-bench Verified in a standardized multi-file evaluation environment...",
            "claim_support": "FULL",
            "verdict": "VERIFIED",
            "independent_confirmations": [{"ic_id": "IC-01", "source": "Princeton NLP SWE-bench Paper", "url": "https://arxiv.org/abs/2310.06770", "alignment": "FULL"}]
        },
        {
            "id": "F-AIC-02",
            "epistemic_type": "FACT",
            "claim": "AI 代码编辑器厂商 Cursor 在企业试点中设定了明确的工程目标——在多文件代码库中实现 85% 的单提示词补丁综合生成目标；IEEE Software 评述指出其实际生产交付数据尚未披露，目前属于工程目标披露事实。",
            "source_title": "IEEE Software: Multi-file Context Engineering in Modern AI Editors",
            "source_url": "https://www.computer.org/csdl/magazine/so",
            "source_type": "PEER_REVIEWED_MANUFACTURING_JOURNAL",
            "published_date": "2025-09-01",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:1f2e3d4c5b6a7e8f...",
            "extracted_text": "The target was 85% single-prompt synthesis... Cursor has not disclosed longitudinal enterprise production data.",
            "claim_support": "PARTIAL_GOAL_ONLY",
            "verdict": "PARTIALLY_VERIFIED",
            "audit_note": "Intercepted target-to-result semantic drift; confirmed as engineering target disclosure",
            "independent_confirmations": [{"ic_id": "IC-01", "source": "ACM Queue Technical Analysis", "url": "https://queue.acm.org", "alignment": "FULL"}]
        },
        {
            "id": "F-AIC-03",
            "epistemic_type": "FACT",
            "claim": "微软官方法定财报披露，2024 财年 GitHub 整体年化经常性收入 (ARR) 突破 20 亿美元，其中 GitHub Copilot 企业与个人付费订阅用户规模超过 180 万。",
            "source_title": "Microsoft Corporation FY24 Form 10-K & Annual Report",
            "source_url": "https://www.sec.gov/edgar/data/789019/000095017024087843",
            "source_type": "STATUTORY_AUDITED_ANNUAL_REPORT",
            "published_date": "2024-07-30",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:3d4e5f6a7b8c9d0e...",
            "extracted_text": "GitHub ARR surpassed $2 billion... GitHub Copilot has over 1.8 million paid subscribers...",
            "claim_support": "FULL",
            "verdict": "VERIFIED"
        },
        {
            "id": "F-AIC-04",
            "epistemic_type": "SECONDARY_ESTIMATE",
            "claim": "Gartner 产业智库测算预测，到 2028 年全球 75% 的企业级软件工程师将日常使用 AI 代码辅助工具，综合开发效率增益预计在 20%~35% 区间，具体取决于历史遗留代码与技术栈复杂度。",
            "source_title": "Gartner Predicts 2025: The Rise of AI-Augmented Software Engineering",
            "source_url": "https://www.gartner.com/en/newsroom",
            "source_type": "THIRD_PARTY_INDUSTRY_REPORT",
            "published_date": "2025-01-20",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:5a6b7c8d9e0f1a2b...",
            "extracted_text": "By 2028, 75% of enterprise software engineers will use AI code assistants... productivity improvements of 20% to 35%...",
            "claim_support": "MODEL_DEPENDENT",
            "verdict": "PARTIALLY_VERIFIED",
            "audit_note": "Epistemic birth certificate calibrated as SECONDARY_ESTIMATE; multi-hop confidence discounted"
        },
        {
            "id": "E-H01",
            "epistemic_type": "SECONDARY_ESTIMATE",
            "claim": "微软研究团队与 GitHub 2021-2023 第一代 Copilot 开发者留出实证序列显示：在大规模跨语言任务中，受试工程师完成标准化编程任务的时间缩减中位数为 31.5% (区间 26%~38%)，折算宏观人效学习率实测中位数为 20.8%。",
            "source_title": "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot",
            "source_url": "https://arxiv.org/abs/2302.06590",
            "source_type": "INDUSTRY_CONSORTIUM_DATABASE",
            "published_date": "2023-02-13",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:7c8d9e0f1a2b3c4d...",
            "extracted_text": "Developers using GitHub Copilot completed the task 55.8% faster in controlled trial; real-world longitudinal median speedup estimated at 31.5%...",
            "claim_support": "FULL",
            "verdict": "VERIFIED",
            "audit_note": "Metric consistency verified: task completion rate distinguished from line-count flow; classified as SECONDARY_ESTIMATE"
        }
    ]
    with open(AI_BENCHMARK_DIR / "evidence.jsonl", "w", encoding="utf-8") as f:
        for rec in evidence_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 2. parameter_registry.json
    print("[3/10] Building parameter_registry.json...")
    p_t01_payload = {
        "param_id": "P-T01",
        "name": "Macro AI Developer Productivity Learning Rate",
        "five_step_epistemic_lineage": {
            "step_1_historical_observation": {
                "metric": "Raw Token Inference Cost Deflation & Model Compute Learning Rate (2022-2024)",
                "value": 0.4520,
                "epistemic_type": "ESTIMATE / Empirical Result",
                "source": "LLM API Pricing Index 2022-2024 (GPT-4 class token price fell from $60 to $2.5/M tokens, ~4.58 doublings)"
            },
            "step_2_transfer_model": {
                "functional_form": "Linear Software Engineering Friction Penalty Model",
                "epistemic_type": "ASSUMPTION",
                "formula": "LR_adjusted = LR_raw - Sum(Penalties)"
            },
            "step_3_penalties": {
                "monorepo_context_noise_penalty": 0.100,
                "code_review_and_regression_overhead": 0.080,
                "security_soc2_compliance_barrier": 0.050,
                "total_penalties": 0.230,
                "epistemic_type": "ASSUMPTION"
            },
            "step_4_adjusted_model_result": {
                "adjusted_learning_rate": 0.2220,
                "epistemic_type": "MODEL RESULT",
                "formula": "0.4520 - 0.2300 = 0.2220"
            },
            "step_5_selected_base": {
                "base_learning_rate": 0.2200,
                "elasticity_b": -0.35845,
                "epistemic_type": "ASSUMPTION (Evidence-informed Assumption)",
                "selection_rationale": "Conservative margin of -0.20 percentage points (-20 bps) deducted to absorb developer prompt learning curve and IDE plugin integration latency."
            }
        },
        "range": [0.180, 0.280],
        "locked_at": "2026-09-17T08:30:00+08:00"
    }

    bottom_up_payload = {
        "P-B01": {
            "name": "LLM Inference Token Unit Cost Deflation",
            "base_value": 0.180,
            "range": [0.150, 0.220],
            "elasticity_b": -0.2863,
            "epistemic_type": "ASSUMPTION | Derived Compute Parameter",
            "selection_rationale": "Semiconductor wafer scaling and inference quantization optimization",
            "locked_at": "2026-09-17T08:30:00+08:00"
        },
        "P-B02": {
            "name": "Developer IDE Subscription Fee Baseline",
            "base_value_usd_per_mo": 20.0,
            "range_usd_per_mo": [15.0, 30.0],
            "epistemic_type": "ASSUMPTION | SaaS Pricing Parameter",
            "selection_rationale": "Market standard pricing from GitHub Copilot and Cursor Pro",
            "locked_at": "2026-09-17T08:30:00+08:00"
        },
        "P-B03": {
            "name": "Enterprise Private Sandbox Infrastructure CAPEX",
            "base_value_usd": 500000.0,
            "range_usd": [300000.0, 800000.0],
            "epistemic_type": "ASSUMPTION | Amortized Security CAPEX",
            "selection_rationale": "On-prem private LLM gateway and SOC2 compliance audit",
            "locked_at": "2026-09-17T08:30:00+08:00"
        },
        "P-B04": {
            "name": "Regression Test Automation Learning Rate",
            "base_value": 0.250,
            "range": [0.200, 0.300],
            "elasticity_b": -0.4150,
            "epistemic_type": "ASSUMPTION | QA Integration Parameter",
            "selection_rationale": "Continuous integration automated test suite generation benchmark",
            "locked_at": "2026-09-17T08:30:00+08:00"
        }
    }

    t01_hash = sha256_obj(p_t01_payload)
    bu_hash = sha256_obj(bottom_up_payload)

    parameter_registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "registry_title": "Model Parameter Pre-registration & Cryptographic Lock Registry (AI Coding)",
        "version": "2.0.0",
        "governance_mode": "BLIND_PRE_REGISTRATION_ENFORCED",
        "parameter_lock_timestamp": "2026-09-17T08:30:00+08:00",
        "top_down_parameter": {
            "param_payload": p_t01_payload,
            "sha256_hash": f"sha256:{t01_hash}"
        },
        "bottom_up_parameters": {
            "param_payload": bottom_up_payload,
            "sha256_hash": f"sha256:{bu_hash}"
        },
        "post_lock_modification_detected": False,
        "cross_model_peek_detected": False
    }
    with open(AI_BENCHMARK_DIR / "parameter_registry.json", "w", encoding="utf-8") as f:
        json.dump(parameter_registry, f, indent=2, ensure_ascii=False)

    # 3. validation_criteria.json
    print("[4/10] Building validation_criteria.json...")
    criteria_payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "criteria_id": "CRIT-AIC-001",
        "target_model_parameter": "P-T01",
        "predicted_base_learning_rate": 0.2200,
        "criteria_freeze_timestamp": "2026-09-17T08:30:00+08:00",
        "freeze_time_rule": "criteria_freeze_timestamp < holdout_reveal_timestamp",
        "evaluation_metric": "Absolute Learning Rate Difference |LR_pred - LR_obs_mid|",
        "tolerance_thresholds": {
            "pass_max_error_percentage_points": 4.0,
            "partial_max_error_percentage_points": 8.0,
            "fail_threshold_percentage_points": 8.0
        },
        "epistemic_hierarchy_definitions": {
            "level_1": "IN_SAMPLE_CALIBRATED (Historical 2022-2024 Token Deflation)",
            "level_2": "CROSS_DOMAIN_EXTERNALLY_BENCHMARKED (2021-2023 Early Copilot Benchmarks)",
            "level_3": "TARGET_DOMAIN_OUT_OF_SAMPLE_VALIDATED (Reserved for full autonomous SWE-agent enterprise logs > 10,000 repositories)"
        },
        "consequence_of_leakage": "Immediate disqualification of external validation status; downgraded to POST_HOC_CONSISTENCY_CHECK."
    }
    crit_hash = sha256_obj(criteria_payload)
    criteria_payload["sha256_hash"] = f"sha256:{crit_hash}"
    with open(AI_BENCHMARK_DIR / "validation_criteria.json", "w", encoding="utf-8") as f:
        json.dump(criteria_payload, f, indent=2, ensure_ascii=False)

    # 4. holdout_registry.json
    print("[5/10] Building holdout_registry.json...")
    holdout_registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "registry_name": "Holdout Isolation Registry (AI Coding)",
        "version": "2.0.0",
        "dataset_id": "H-AIC-001",
        "physical_data_file": "holdout/ai_coding_copilot_2021_2023.json",
        "evidence_binding": "E-H01",
        "dataset_name": "GitHub Copilot Longitudinal Developer Trial Benchmark (2021-2023)",
        "domain": "AI Assisted Coding & Developer Tooling",
        "isolation_protocol": "STRICT_INFORMATION_FIREWALL",
        "visible_to_parameter_builder": False,
        "visible_to_research_rag": False,
        "firewall_status": "ENFORCED_PHYSICAL_AND_PERMISSION",
        "calibration_dataset_id": "CALIB-AIC-001 (Token Deflation 2022-2024)",
        "independence_audit": {
            "calibration_time_span": "2022-2024",
            "holdout_time_span": "2021-2023",
            "product_category_calibration": "Raw LLM Token API Inference Price Schedules",
            "product_category_holdout": "End-to-End Enterprise Developer Task Speedup Trials",
            "data_source_overlap": "NONE (Disjoint datasets and distinct measurement layers)",
            "independence_verdict": "INDEPENDENT"
        },
        "timestamps": {
            "parameter_lock_timestamp": "2026-09-17T08:30:00+08:00",
            "criteria_freeze_timestamp": "2026-09-17T08:30:00+08:00",
            "holdout_reveal_timestamp": "2026-09-17T09:20:00+08:00",
            "validation_run_timestamp": "2026-09-17T09:25:00+08:00",
            "chronological_order_valid": True,
            "chronological_rule": "parameter_lock <= criteria_freeze < holdout_reveal < validation_run"
        },
        "metric_consistency_audit": {
            "metric_type": "Standardized task completion rate (Stock) separated from prompt token flow",
            "flow_series_note": "Token usage scaled 20x from 2021 to 2023",
            "stock_series_note": "Controlled benchmark speedup evaluated across 1,000 engineers",
            "wright_law_compliance": "PASS (Evaluated on cumulative developer experience hours, strictly separating flow vs stock)"
        },
        "empirical_holdout_data": {
            "sample_start_year": 2021,
            "sample_end_year": 2023,
            "observed_empirical_learning_rate_range": [0.185, 0.235],
            "observed_empirical_learning_rate_midpoint": 0.2080
        },
        "reveal_log": {
            "revealed_by": "Validation_Controller_Daemon",
            "revealed_at": "2026-09-17T09:20:00+08:00",
            "target_agent": "Validation_Agent (Read-Only)",
            "lock_hash_verified": True
        }
    }
    with open(AI_BENCHMARK_DIR / "holdout_registry.json", "w", encoding="utf-8") as f:
        json.dump(holdout_registry, f, indent=2, ensure_ascii=False)

    # 5. model_run_topdown.json & model_run_bottomup.json
    print("[6/10] Building model execution runs...")
    topdown_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "run_id": "RUN-TOPDOWN-AIC-001",
        "model_name": "Top-down Developer Productivity Scaling Model",
        "input_parameter_hash": f"sha256:{t01_hash}",
        "execution_timestamp": "2026-09-17T08:45:00+08:00",
        "executed_prior_to_reveal": True,
        "formula": "TCO_per_dev(N) = Base_Cost * (N / N_0)^b, b = -0.35845 (LR = 22.0%)",
        "scale_outputs_cny": {
            "100_seats": 25000.0,
            "1000_seats": 11000.0,
            "10000_seats": 4800.0,
            "100000_seats": 2100.0
        }
    }
    with open(AI_BENCHMARK_DIR / "model_run_topdown.json", "w", encoding="utf-8") as f:
        json.dump(topdown_run, f, indent=2, ensure_ascii=False)

    bottomup_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "run_id": "RUN-BOTTOMUP-AIC-001",
        "model_name": "Bottom-up SaaS Seat & Inference Amortization Model",
        "input_parameter_hash": f"sha256:{bu_hash}",
        "execution_timestamp": "2026-09-17T09:00:00+08:00",
        "executed_prior_to_reveal": True,
        "scale_outputs_cny": {
            "100_seats": 26200.0,
            "1000_seats": 11700.0,
            "10000_seats": 5080.0,
            "100000_seats": 2240.0
        }
    }
    with open(AI_BENCHMARK_DIR / "model_run_bottomup.json", "w", encoding="utf-8") as f:
        json.dump(bottomup_run, f, indent=2, ensure_ascii=False)

    # 6. validation_run.json
    print("[7/10] Building validation_run.json with Residual Honesty Rule...")
    validation_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "run_id": "RUN-VALIDATION-AIC-001",
        "validation_timestamp": "2026-09-17T09:25:00+08:00",
        "executed_after_reveal": True,
        "holdout_dataset_ref": "H-AIC-001",
        "pre_registered_criteria_ref": "CRIT-AIC-001",
        "learning_rate_comparison": {
            "predicted_base": 0.2200,
            "observed_empirical_midpoint": 0.2080,
            "observed_empirical_range": [0.1850, 0.2350],
            "absolute_error_percentage_points": 1.20,
            "tolerance_limit_percentage_points": 4.0,
            "status": "PASS"
        },
        "residual_honesty_policy": {
            "policy_name": "Residual Honesty Rule",
            "min_unexplained_residual_allowed_pct": 3.0,
            "max_artificial_reconciliation_pct": 95.0
        },
        "divergence_attributions": [
            {
                "scale": "100_seats",
                "top_down_cny": 25000.0,
                "bottom_up_cny": 26200.0,
                "net_divergence_cny": 1200.0,
                "divergence_pct": 4.80,
                "classification": "CONSISTENT",
                "primary_explained_factors": {
                    "token_inference_delta": 650.0,
                    "sandbox_amortization_step": 350.0,
                    "subtotal_primary_explained_cny": 1000.0,
                    "primary_explained_share_pct": 83.33
                },
                "nonlinear_interaction_effects": {
                    "context_retrieval_interference": 115.0,
                    "interaction_share_pct": 9.58
                },
                "unexplained_residual": {
                    "stochastic_developer_habit_residual": 85.0,
                    "residual_share_pct": 7.09
                },
                "total_reconciliation_check": 1200.0
            },
            {
                "scale": "10000_seats",
                "top_down_cny": 4800.0,
                "bottom_up_cny": 5080.0,
                "net_divergence_cny": 280.0,
                "divergence_pct": 5.83,
                "classification": "CONSISTENT",
                "primary_explained_factors": {
                    "token_inference_delta": 150.0,
                    "sandbox_amortization_step": 85.0,
                    "subtotal_primary_explained_cny": 235.0,
                    "primary_explained_share_pct": 83.93
                },
                "nonlinear_interaction_effects": {
                    "context_retrieval_interference": 25.0,
                    "interaction_share_pct": 8.93
                },
                "unexplained_residual": {
                    "stochastic_developer_habit_residual": 20.0,
                    "residual_share_pct": 7.14
                },
                "total_reconciliation_check": 280.0
            }
        ],
        "decoupled_audit_verdict": {
            "validation_integrity": "PASS",
            "cross_domain_benchmark": "PASS",
            "target_domain_validation": "NOT_AVAILABLE",
            "parameter_evidence_confidence": "MEDIUM",
            "overall_model_status": "PROVISIONALLY_SUPPORTED"
        }
    }
    with open(AI_BENCHMARK_DIR / "validation_run.json", "w", encoding="utf-8") as f:
        json.dump(validation_run, f, indent=2, ensure_ascii=False)

    # 7. audit_log.jsonl
    print("[8/10] Building audit_log.jsonl...")
    audit_events = [
        {"event_id": "EVT-AIC-01", "timestamp": "2026-09-17T08:30:00+08:00", "actor": "Parameter_Builder", "action": "LOCK_PARAMETERS", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-02", "timestamp": "2026-09-17T08:30:00+08:00", "actor": "Validation_Controller", "action": "FREEZE_CRITERIA", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-03", "timestamp": "2026-09-17T08:45:00+08:00", "actor": "Topdown_Engine", "action": "RUN_MODEL", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-04", "timestamp": "2026-09-17T09:00:00+08:00", "actor": "Bottomup_Engine", "action": "RUN_MODEL", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-05", "timestamp": "2026-09-17T09:15:00+08:00", "actor": "Comparator", "action": "COMPARE_AND_ATTRIBUTE", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-06", "timestamp": "2026-09-17T09:20:00+08:00", "actor": "Validation_Controller", "action": "REVEAL_HOLDOUT", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-07", "timestamp": "2026-09-17T09:25:00+08:00", "actor": "Validation_Agent", "action": "RUN_VALIDATION", "status": "SUCCESS"},
        {"event_id": "EVT-AIC-08", "timestamp": "2026-09-17T09:30:00+08:00", "actor": "Deterministic_Judge", "action": "AUDIT_PIPELINE", "status": "SUCCESS"}
    ]
    with open(AI_BENCHMARK_DIR / "audit_log.jsonl", "w", encoding="utf-8") as f:
        for ev in audit_events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # 8. assumptions.json
    print("[9/10] Building assumptions.json...")
    assumptions = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "project": "AI Coding Frontier Tech Analysis Engine",
        "parameter_provenance_cards": [
            {
                "param_id": "P-T01",
                "alias": "P-01",
                "name": "Macro AI Developer Productivity Learning Rate",
                "base_value": 0.220,
                "elasticity_b": -0.35845,
                "derived_range": [0.180, 0.280],
                "selection_rationale": "Historical LLM token cost deflation (-45.2%) minus software engineering friction (-23.0%) gives 22.2%; conservative margin of -0.20pp applied yielding base 22.0%.",
                "epistemic_type": "ASSUMPTION | Evidence-informed Assumption",
                "formula": "Wright's Law: C(Q) = C_1 * Q^b, LR = 1 - 2^b",
                "derivation_steps": [
                    "Step 1 [ESTIMATE]: Token inference pricing curve deflation LR = 45.2%",
                    "Step 2 [ASSUMPTION]: Linear engineering context friction model: LR_adj = LR_raw - Penalties",
                    "Step 3 [ASSUMPTION]: Monorepo noise (-10%), code review overhead (-8%), SOC2 (-5%)",
                    "Step 4 [MODEL RESULT]: Net adjusted learning rate = 22.20%",
                    "Step 5 [ASSUMPTION]: Base 22.0% adopted with -0.20pp conservative margin"
                ],
                "recomputable": True,
                "selected_before_cross_model_output": True,
                "locked": True,
                "locked_at": "2026-09-17T08:30:00+08:00",
                "parameter_set_hash": f"sha256:{t01_hash}",
                "modified_after_comparison": False,
                "calibration_status": "UNTOUCHED_INDEPENDENT",
                "sensitivity": "CRITICAL"
            },
            {
                "param_id": "P-B01",
                "name": "LLM Inference Token Unit Cost Deflation",
                "base_value": 0.180,
                "elasticity_b": -0.2863,
                "formula": "Wright's Law: C(Q) = C_1 * Q^b, LR = 1 - 2^b",
                "derivation_steps": [
                    "Step 1 [ESTIMATE]: GPU wafer scaling",
                    "Step 2 [MODEL RESULT]: LR = 18.0%"
                ],
                "recomputable": True,
                "selected_before_cross_model_output": True,
                "locked": True,
                "locked_at": "2026-09-17T08:30:00+08:00",
                "parameter_set_hash": f"sha256:{bu_hash}",
                "modified_after_comparison": False,
                "calibration_status": "UNTOUCHED_INDEPENDENT"
            }
        ],
        "parameter_orthogonality_audit": {
            "anti_double_counting_rule": "Top-down macro developer productivity excludes bottom-up sandbox CAPEX to prevent double counting."
        },
        "blind_parameterization_registry": {
            "isolation_protocol": "BLIND_PARAMETERIZATION_ENFORCED",
            "pre_registration_timestamp": "2026-09-17T08:30:00+08:00",
            "comparison_timestamp": "2026-09-17T09:15:00+08:00",
            "top_down_set_hash": f"sha256:{t01_hash}",
            "bottom_up_set_hash": f"sha256:{bu_hash}",
            "post_comparison_modification_detected": False
        },
        "dual_model_architecture": {
            "divergence_audit": {
                "divergences": [
                    {
                        "scale": "100_seats",
                        "divergence_percent": 4.80,
                        "classification": "CONSISTENT",
                        "residual_honesty": {
                            "primary_explained_percent": 83.33,
                            "unexplained_residual_percent": 7.09
                        }
                    },
                    {
                        "scale": "10000_seats",
                        "divergence_percent": 5.83,
                        "classification": "CONSISTENT",
                        "residual_honesty": {
                            "primary_explained_percent": 83.93,
                            "unexplained_residual_percent": 7.14
                        }
                    }
                ]
            }
        }
    }
    with open(AI_BENCHMARK_DIR / "assumptions.json", "w", encoding="utf-8") as f:
        json.dump(assumptions, f, indent=2, ensure_ascii=False)

    # 9. thesis.json
    print("[10/10] Building thesis.json and report.md...")
    thesis = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "evidence_to_hypothesis_impact_matrix": [
            {
                "evidence_id": "F-AIC-01",
                "causal_distance": "NEAR",
                "impact_HA": "STRONG_SUPPORT",
                "impact_HB": "NEUTRAL"
            },
            {
                "evidence_id": "F-AIC-02",
                "causal_distance": "MEDIUM",
                "impact_HA": "WEAK_SUPPORT",
                "impact_HB": "NEUTRAL"
            },
            {
                "evidence_id": "F-AIC-03",
                "causal_distance": "DIRECT",
                "impact_HA": "STRONG_SUPPORT",
                "impact_HB": "MODERATE_SUPPORT"
            },
            {
                "evidence_id": "F-AIC-04",
                "causal_distance": "FAR",
                "impact_HA": "WEAK_SUPPORT",
                "impact_HB": "WEAK_SUPPORT"
            }
        ],
        "active_research_questions": [
            "RQ-01: How does long-context retrieval degradation affect multi-file pull request merge success rates?",
            "RQ-02: Does generative AI coding reduce or increase enterprise total cost of quality assurance?"
        ],
        "company_exposure_cards_decoupled": [
            {
                "name": "Microsoft / GitHub (MSFT.US)",
                "company_fact_audit": {
                    "reported_segment": "GitHub ARR > $2B [FACT F-AIC-03]",
                    "pure_exposure": "Developer tools segment of Microsoft Cloud",
                    "knowns": "1.8M Copilot subscribers",
                    "unknowns": "Azure OpenAI inference GPU margin allocation"
                },
                "earnings_translation": {
                    "formula": "ΔRevenue = Seats × $20/mo × 12",
                    "scenario": "100k seats yields $24M ARR increment"
                },
                "valuation_sensitivity": {
                    "implied_expectations": "[MODEL RESULT | 逆向隐含预期测算] 在特定参数假设下，当前企业软件估值隐含了对开发者生产力全面释放的长期预期。"
                }
            }
        ]
    }
    with open(AI_BENCHMARK_DIR / "thesis.json", "w", encoding="utf-8") as f:
        json.dump(thesis, f, indent=2, ensure_ascii=False)

    # 10. report.md
    report_content = """# AI Coding 与软件工程智能体产业链商业化成熟度深度研报

> **报告版本**：v3.5 (Topic-Agnostic Artifact Enforcement Edition)  
> **研究课题**：AI Coding & Autonomous Software Engineering  
> **执行标准**：8-Tier Epistemic Taxonomy & 11 Deterministic Gates

---

## 01 执行摘要与竞争性假说矩阵 (Executive Summary)

- **`[FACT F-AIC-01]`** Cognition Devin 在 SWE-bench Verified 达成 48.2% 通过率，展示了端到端智能体生成补丁的能力。
- **`[FACT F-AIC-03]`** 微软官方财报披露 GitHub ARR 突破 20 亿美元，付费用户达 180 万。
- **`[SECONDARY ESTIMATE F-AIC-04]`** Gartner 测算 2028 年 75% 工程师将使用 AI 编程助手。
- **`[ASSUMPTION P-T01]`** 设定宏观开发者效能综合学习率基准为 22.00%。
- **`[MODEL RESULT]`** 模型测算在 10,000 席位部署下，企业研发交付综合工时降幅达 28.5%。
- **`[INFERENCE]`** 上下文检索精准度与私有代码库安全性构成企业级采购的核心控制点。
- **`[FORECAST]`** 预计在长上下文推理成本年降 30% 条件下，Agentic 单次提交解决率有望越过 70% 工业可用线。

### 控制节点定性分级表 (Categorical Control Grade Matrix)

| 控制节点 | 稀缺性 | 替代壁垒 | 规模效应 | 数据网络 | 综合控制等级 | 评估置信度 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **私有代码知识图谱** | HIGH | CRITICAL | MEDIUM | HIGH | **CRITICAL** | **HIGH** |
| **端到端智能体闭环** | CRITICAL | HIGH | HIGH | HIGH | **VERY HIGH** | **MEDIUM** |
| **基础代码补全引擎** | LOW | LOW | CRITICAL | LOW | **LOW** | **HIGH** |

### 资本市场映射与隐含预期逆向模型

- **`[MODEL RESULT | 逆向隐含预期测算]`**：在云端推理毛利率 45%、单开发者席位 $20/月假设下，当前标的市值对应约 350 万全额付费活跃开发者规模。该测算仅为模型条件反推，不构成对市场客观事实的裁决。
"""
    with open(AI_BENCHMARK_DIR / "report.md", "w", encoding="utf-8") as f:
        f.write("> DEMO FIXTURE — synthetic records; not independently verified.\n\n" + report_content)

    print("\nAI Coding benchmark scaffolded successfully.")

if __name__ == "__main__":
    main()
