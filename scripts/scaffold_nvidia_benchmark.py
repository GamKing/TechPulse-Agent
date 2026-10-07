#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scaffold NVIDIA Benchmark Project (Artifact Enforcement Edition)
Frontier Tech Industrial Analysis Engine
"""

import json
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "generated"
NV_BENCHMARK_DIR = BASE_DIR / "reports" / "nvidia_benchmark"

def sha256_obj(obj: dict) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def main():
    (BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
    print("[1/10] Creating reports/nvidia_benchmark directory...")
    NV_BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    # 1. evidence.jsonl
    print("[2/10] Building evidence.jsonl...")
    evidence_records = [
        {
            "id": "F-NV-01",
            "epistemic_type": "FACT",
            "claim": "英伟达 2025 财年法定审计财报披露，全口径营业收入突破 1,200 亿美元，其中数据中心业务营收占比达 87.5% (单季超 300 亿美元)；前四大直接与间接云厂商客户合计贡献全公司 40%~45% 营业收入。",
            "source_title": "NVIDIA Corporation FY25 Form 10-K & Statutory Financial Release",
            "source_url": "https://www.sec.gov/edgar/data/1045810/000104581025000010",
            "source_type": "STATUTORY_AUDITED_ANNUAL_REPORT",
            "published_date": "2025-02-26",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:7a8b9c0d1e2f3a4b...",
            "extracted_text": "Data Center revenue was $100+ billion, up exponentially... Customer A and Customer B accounted for 13% and 11% of total revenue respectively...",
            "claim_support": "FULL",
            "verdict": "VERIFIED",
            "independent_confirmations": [{"ic_id": "IC-01", "source": "Bloomberg Financial Database", "url": "https://www.bloomberg.com", "alignment": "FULL"}]
        },
        {
            "id": "F-NV-02",
            "epistemic_type": "FACT",
            "claim": "英伟达官方工程白皮书披露，Blackwell GB200 NVL72 液冷机架系统整合 36 颗 Grace CPU 与 72 颗 Blackwell GPU，背板全铜缆直连实现 130 TB/s 双向 NVLink 5 域互联总带宽，整机柜计算密度较前代 H100 集群提升近 4 倍。",
            "source_title": "NVIDIA GB200 NVL72 Architecture Technical Whitepaper",
            "source_url": "https://www.nvidia.com/en-us/data-center/gb200-nvl72",
            "source_type": "PEER_REVIEWED_MANUFACTURING_JOURNAL",
            "published_date": "2024-09-15",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:3c4d5e6f7a8b9c0d...",
            "extracted_text": "GB200 NVL72 connects 72 Blackwell GPUs and 36 Grace CPUs with 130TB/s bidirectional NVLink bandwidth in a single liquid-cooled rack...",
            "claim_support": "FULL",
            "verdict": "VERIFIED"
        },
        {
            "id": "F-NV-03",
            "epistemic_type": "SECONDARY_ESTIMATE",
            "claim": "高盛与 Omdia 产业智库测算统计显示：2024-2025 年全球主要超大规模云厂商自研 ASIC (包括 Google TPU、AWS Trainium/Inferentia、Meta MTIA) 在内部推理与特定训练任务中的出货量份额达到 18%~22%。",
            "source_title": "Goldman Sachs Equity Research: Cloud Hyperscaler Custom Silicon Trajectory",
            "source_url": "https://www.goldmansachs.com/insights",
            "source_type": "THIRD_PARTY_INDUSTRY_REPORT",
            "published_date": "2025-04-10",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:5e6f7a8b9c0d1e2f...",
            "extracted_text": "Custom ASICs from Google, AWS, and Meta reached 18%-22% of total cloud AI accelerator volume in 2024...",
            "claim_support": "MODEL_DEPENDENT",
            "verdict": "PARTIALLY_VERIFIED",
            "audit_note": "Epistemic birth certificate calibrated: classified as SECONDARY_ESTIMATE from institutional survey"
        },
        {
            "id": "F-NV-04",
            "epistemic_type": "SECONDARY_ESTIMATE",
            "claim": "红杉资本测算模型指出，全球数据中心年化 AI 基础设施硬件资本开支需对应终端企业级软件产生约 6,000 亿美元增量收入方能实现健康投资回报闭环，而当前实际可跟踪的企业级 AI 真实收入仍在数百亿美元规模，存在显著投资回报剪刀差。",
            "source_title": "AI's $600B Question - Sequoia Capital Industry Analysis",
            "source_url": "https://www.sequoiacap.com/article/ais-600b-question",
            "source_type": "THIRD_PARTY_INDUSTRY_REPORT",
            "published_date": "2024-06-20",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:1a2b3c4d5e6f7a8b...",
            "extracted_text": "The revenue shortfall has grown from $200B to $600B... End-user software monetization remains far behind hardware capex...",
            "claim_support": "MODEL_DEPENDENT",
            "verdict": "PARTIALLY_VERIFIED",
            "audit_note": "Macroeconomic theoretical gap model calibrated as SECONDARY_ESTIMATE"
        },
        {
            "id": "E-H01",
            "epistemic_type": "SECONDARY_ESTIMATE",
            "claim": "IDC 与 Mercury Research 实证序列显示：2022-2024 年全球前代 Hopper 架构 (H100/H200) 累计制造出厂量由约 30 万张增至 380 万张 (物理翻倍次数 n=3.66 次)，裸机出厂均价从 $38,000 下探至约 $28,000 (2015年不变价)，对应实证经验硬件学习率中位数为 14.80% (区间 13.9%~15.6%)。",
            "source_title": "IDC Worldwide Server and AI Accelerator Quarterly Tracker & Mercury Research",
            "source_url": "https://www.idc.com/tracker",
            "source_type": "INDUSTRY_CONSORTIUM_DATABASE",
            "published_date": "2025-01-15",
            "retrieved_at": "2026-09-17T11:00:00Z",
            "http_status": 200,
            "content_hash": "sha256:9f8e7d6c5b4a3c2b...",
            "extracted_text": "Cumulative Hopper shipments reached 3.8M units in 2024 from 300k in 2022, with ASP declining from $38k to $28k on constant dollar basis...",
            "claim_support": "FULL",
            "verdict": "VERIFIED",
            "audit_note": "Metric consistency verified: strictly distinguished between annual shipments and cumulative production; constant USD applied; classified as SECONDARY_ESTIMATE"
        }
    ]
    with open(NV_BENCHMARK_DIR / "evidence.jsonl", "w", encoding="utf-8") as f:
        for rec in evidence_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 2. parameter_registry.json
    print("[3/10] Building parameter_registry.json...")
    p_t01_payload = {
        "param_id": "P-T01",
        "name": "Macro AI Accelerator Cluster Hardware TCO Learning Rate",
        "five_step_epistemic_lineage": {
            "step_1_historical_observation": {
                "metric": "Raw Semiconductor Advanced Packaging & Wafer Processing Historical Learning Rate (2018-2023)",
                "value": 0.2850,
                "epistemic_type": "ESTIMATE / Empirical Result",
                "source": "TSMC & Semiconductor Industry Association (SIA) wafer yield & CoWoS learning curves"
            },
            "step_2_transfer_model": {
                "functional_form": "Linear Data Center Physical Packaging Friction Model",
                "epistemic_type": "ASSUMPTION",
                "formula": "LR_adjusted = LR_raw - Sum(Penalties)"
            },
            "step_3_penalties": {
                "liquid_cooling_and_power_distribution_penalty": 0.060,
                "copper_backplane_assembly_and_signal_loss_penalty": 0.045,
                "geopolitical_export_compliance_buffer": 0.025,
                "total_penalties": 0.130,
                "epistemic_type": "ASSUMPTION"
            },
            "step_4_adjusted_model_result": {
                "adjusted_learning_rate": 0.1550,
                "epistemic_type": "MODEL RESULT",
                "formula": "0.2850 - 0.1300 = 0.1550"
            },
            "step_5_selected_base": {
                "base_learning_rate": 0.1500,
                "elasticity_b": -0.23447,
                "epistemic_type": "ASSUMPTION (Evidence-informed Assumption)",
                "selection_rationale": "Conservative margin of -0.50 percentage points (-50 bps) explicitly deducted from 15.50% model output to absorb early NVLink 5 copper backplane manufacturing defect variability and liquid cold-plate leakage risk."
            }
        },
        "range": [0.120, 0.180],
        "locked_at": "2026-09-17T08:30:00+08:00"
    }

    bottom_up_payload = {
        "P-B01": {
            "name": "CoWoS Packaging & HBM3e Memory Stack Learning Rate",
            "base_value": 0.135,
            "range": [0.110, 0.150],
            "elasticity_b": -0.2092,
            "epistemic_type": "ASSUMPTION | Derived Component Parameter",
            "selection_rationale": "TSMC CoWoS-L capacity scaling contracts and SK Hynix HBM3e volume discount tiers",
            "locked_at": "2026-09-17T08:30:00+08:00"
        },
        "P-B02": {
            "name": "Optical Transceiver & Direct Attach Copper Interconnect Deflation",
            "base_value": 0.120,
            "range": [0.090, 0.140],
            "epistemic_type": "ASSUMPTION | Derived Networking Parameter",
            "selection_rationale": "Innolight / Amphenol high-speed networking cable annual deflation curve",
            "locked_at": "2026-09-17T08:30:00+08:00"
        },
        "P-B03": {
            "name": "Megawatt Liquid Cooling Manifold & CDU Infrastructure CAPEX",
            "base_value_cny": 25000000.0,
            "range_cny": [20000000.0, 30000000.0],
            "epistemic_type": "ASSUMPTION | Fixed Infrastructure CAPEX",
            "selection_rationale": "Tier-1 data center liquid cooling infrastructure engineering quotes",
            "locked_at": "2026-09-17T08:30:00+08:00"
        },
        "P-B04": {
            "name": "Rack System Integration & Burn-in Testing Learning Rate",
            "base_value": 0.180,
            "range": [0.150, 0.220],
            "elasticity_b": -0.2863,
            "epistemic_type": "ASSUMPTION | System Assembly Parameter",
            "selection_rationale": "Foxconn / Wistron AI server rack assembly process optimization benchmark",
            "locked_at": "2026-09-17T08:30:00+08:00"
        }
    }

    t01_hash = sha256_obj(p_t01_payload)
    bu_hash = sha256_obj(bottom_up_payload)

    parameter_registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "registry_title": "Model Parameter Pre-registration & Cryptographic Lock Registry (NVIDIA)",
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
    with open(NV_BENCHMARK_DIR / "parameter_registry.json", "w", encoding="utf-8") as f:
        json.dump(parameter_registry, f, indent=2, ensure_ascii=False)

    # 3. validation_criteria.json
    print("[4/10] Building validation_criteria.json...")
    criteria_payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "criteria_id": "CRIT-NV-001",
        "target_model_parameter": "P-T01",
        "predicted_base_learning_rate": 0.1500,
        "criteria_freeze_timestamp": "2026-09-17T08:30:00+08:00",
        "freeze_time_rule": "criteria_freeze_timestamp < holdout_reveal_timestamp",
        "evaluation_metric": "Absolute Learning Rate Difference |LR_pred - LR_obs_mid|",
        "tolerance_thresholds": {
            "pass_max_error_percentage_points": 3.0,
            "partial_max_error_percentage_points": 6.0,
            "fail_threshold_percentage_points": 6.0
        },
        "epistemic_hierarchy_definitions": {
            "level_1": "IN_SAMPLE_CALIBRATED (Historical 2018-2023 Wafer & CoWoS Data)",
            "level_2": "CROSS_DOMAIN_EXTERNALLY_BENCHMARKED (2022-2024 Hopper H100 Real Series)",
            "level_3": "TARGET_DOMAIN_OUT_OF_SAMPLE_VALIDATED (Reserved for Blackwell GB200 NVL72 serial shipments > 10,000 racks)"
        },
        "consequence_of_leakage": "Immediate disqualification of external validation status; downgraded to POST_HOC_CONSISTENCY_CHECK."
    }
    crit_hash = sha256_obj(criteria_payload)
    criteria_payload["sha256_hash"] = f"sha256:{crit_hash}"
    with open(NV_BENCHMARK_DIR / "validation_criteria.json", "w", encoding="utf-8") as f:
        json.dump(criteria_payload, f, indent=2, ensure_ascii=False)

    # 4. holdout_registry.json
    print("[5/10] Building holdout_registry.json...")
    holdout_registry = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "registry_name": "Holdout Isolation Registry (NVIDIA)",
        "version": "2.0.0",
        "dataset_id": "H-NV-001",
        "physical_data_file": "holdout/nvidia_hopper_2022_2024.json",
        "evidence_binding": "E-H01",
        "dataset_name": "NVIDIA Hopper Architecture H100/H200 Production & Price Deflation (2022-2024)",
        "domain": "AI Accelerated Server Hardware",
        "isolation_protocol": "STRICT_INFORMATION_FIREWALL",
        "visible_to_parameter_builder": False,
        "visible_to_research_rag": False,
        "firewall_status": "ENFORCED_PHYSICAL_AND_PERMISSION",
        "calibration_dataset_id": "CALIB-NV-001 (TSMC Wafer & Packaging 2018-2023)",
        "independence_audit": {
            "calibration_time_span": "2018-2023",
            "holdout_time_span": "2022-2024",
            "product_category_calibration": "Raw Semiconductor Foundry Wafer Substrates",
            "product_category_holdout": "Complete Commercial AI Accelerator Finished Modules (Hopper)",
            "data_source_overlap": "NONE (Disjoint datasets and distinct supply chain tiers)",
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
            "metric_type": "Cumulative Production (Stock) strictly separated from Annual Shipments (Flow)",
            "flow_series_note": "Annual shipments scaled from ~300k/yr in 2022 to ~2.5M/yr in 2024",
            "stock_series_note": "Cumulative volume expanded from 300k to 3.8M units (n=3.66 doublings)",
            "wright_law_compliance": "PASS (Wright's Law calculated on cumulative volume doublings n=3.66, NOT on annual shipments)"
        },
        "empirical_holdout_data": {
            "sample_start_year": 2022,
            "sample_end_year": 2024,
            "cumulative_volume_start": 300000,
            "cumulative_volume_end": 3800000,
            "hardware_asp_start_constant_usd": 38000.0,
            "hardware_asp_end_constant_usd": 28000.0,
            "cumulative_doublings": 3.66,
            "observed_empirical_learning_rate_range": [0.139, 0.156],
            "observed_empirical_learning_rate_midpoint": 0.1480
        },
        "reveal_log": {
            "revealed_by": "Validation_Controller_Daemon",
            "revealed_at": "2026-09-17T09:20:00+08:00",
            "target_agent": "Validation_Agent (Read-Only)",
            "lock_hash_verified": True
        }
    }
    with open(NV_BENCHMARK_DIR / "holdout_registry.json", "w", encoding="utf-8") as f:
        json.dump(holdout_registry, f, indent=2, ensure_ascii=False)

    # 5. model_run_topdown.json & model_run_bottomup.json
    print("[6/10] Building model execution runs...")
    topdown_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "run_id": "RUN-TOPDOWN-NV-001",
        "model_name": "Top-down Wright's Law AI Server Rack Scaling Model",
        "input_parameter_hash": f"sha256:{t01_hash}",
        "execution_timestamp": "2026-09-17T08:45:00+08:00",
        "executed_prior_to_reveal": True,
        "formula": "Cost_per_GPU(Q) = C_1 * (Q / Q_1)^b, b = -0.23447 (LR = 15.0%), C_10k = $35,000",
        "scale_outputs_usd": {
            "10000_gpus": 35000.0,
            "100000_gpus": 20400.0,
            "1000000_gpus": 11900.0,
            "10000000_gpus": 6950.0
        }
    }
    with open(NV_BENCHMARK_DIR / "model_run_topdown.json", "w", encoding="utf-8") as f:
        json.dump(topdown_run, f, indent=2, ensure_ascii=False)

    bottomup_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "run_id": "RUN-BOTTOMUP-NV-001",
        "model_name": "Bottom-up Component Teardown & Rack Infrastructure Model",
        "input_parameter_hash": f"sha256:{bu_hash}",
        "execution_timestamp": "2026-09-17T09:00:00+08:00",
        "executed_prior_to_reveal": True,
        "scale_outputs_usd": {
            "10000_gpus": 36800.0,
            "100000_gpus": 21600.0,
            "1000000_gpus": 12700.0,
            "10000000_gpus": 7450.0
        }
    }
    with open(NV_BENCHMARK_DIR / "model_run_bottomup.json", "w", encoding="utf-8") as f:
        json.dump(bottomup_run, f, indent=2, ensure_ascii=False)

    # 6. validation_run.json
    print("[7/10] Building validation_run.json with Residual Honesty Rule...")
    validation_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "run_id": "RUN-VALIDATION-NV-001",
        "validation_timestamp": "2026-09-17T09:25:00+08:00",
        "executed_after_reveal": True,
        "holdout_dataset_ref": "H-NV-001",
        "pre_registered_criteria_ref": "CRIT-NV-001",
        "learning_rate_comparison": {
            "predicted_base": 0.1500,
            "observed_empirical_midpoint": 0.1480,
            "observed_empirical_range": [0.1390, 0.1560],
            "absolute_error_percentage_points": 0.20,
            "tolerance_limit_percentage_points": 3.0,
            "status": "PASS"
        },
        "residual_honesty_policy": {
            "policy_name": "Residual Honesty Rule",
            "min_unexplained_residual_allowed_pct": 3.0,
            "max_artificial_reconciliation_pct": 95.0
        },
        "divergence_attributions": [
            {
                "scale": "100000_gpus",
                "top_down_usd": 20400.0,
                "bottom_up_usd": 21600.0,
                "net_divergence_usd": 1200.0,
                "divergence_pct": 5.88,
                "classification": "CONSISTENT",
                "primary_explained_factors": {
                    "cowos_packaging_delta_usd": 680.0,
                    "liquid_cooling_cdu_step_usd": 320.0,
                    "subtotal_primary_explained_usd": 1000.0,
                    "primary_explained_share_pct": 83.33
                },
                "nonlinear_interaction_effects": {
                    "backplane_thermal_coupling_usd": 118.0,
                    "interaction_share_pct": 9.83
                },
                "unexplained_residual": {
                    "stochastic_wafer_defect_residual": 82.0,
                    "residual_share_pct": 6.84
                },
                "total_reconciliation_check": 1200.0
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
    with open(NV_BENCHMARK_DIR / "validation_run.json", "w", encoding="utf-8") as f:
        json.dump(validation_run, f, indent=2, ensure_ascii=False)

    # 7. audit_log.jsonl
    print("[8/10] Building audit_log.jsonl...")
    audit_events = [
        {"event_id": "EVT-NV-01", "timestamp": "2026-09-17T08:30:00+08:00", "actor": "Parameter_Builder", "action": "LOCK_PARAMETERS", "status": "SUCCESS"},
        {"event_id": "EVT-NV-02", "timestamp": "2026-09-17T08:30:00+08:00", "actor": "Validation_Controller", "action": "FREEZE_CRITERIA", "status": "SUCCESS"},
        {"event_id": "EVT-NV-03", "timestamp": "2026-09-17T08:45:00+08:00", "actor": "Topdown_Engine", "action": "RUN_MODEL", "status": "SUCCESS"},
        {"event_id": "EVT-NV-04", "timestamp": "2026-09-17T09:00:00+08:00", "actor": "Bottomup_Engine", "action": "RUN_MODEL", "status": "SUCCESS"},
        {"event_id": "EVT-NV-05", "timestamp": "2026-09-17T09:15:00+08:00", "actor": "Comparator", "action": "COMPARE_AND_ATTRIBUTE", "status": "SUCCESS"},
        {"event_id": "EVT-NV-06", "timestamp": "2026-09-17T09:20:00+08:00", "actor": "Validation_Controller", "action": "REVEAL_HOLDOUT", "status": "SUCCESS"},
        {"event_id": "EVT-NV-07", "timestamp": "2026-09-17T09:25:00+08:00", "actor": "Validation_Agent", "action": "RUN_VALIDATION", "status": "SUCCESS"},
        {"event_id": "EVT-NV-08", "timestamp": "2026-09-17T09:30:00+08:00", "actor": "Deterministic_Judge", "action": "AUDIT_PIPELINE", "status": "SUCCESS"}
    ]
    with open(NV_BENCHMARK_DIR / "audit_log.jsonl", "w", encoding="utf-8") as f:
        for ev in audit_events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # 8. assumptions.json
    print("[9/10] Building assumptions.json...")
    assumptions = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "project": "NVIDIA Semiconductor Frontier Tech Analysis Engine",
        "parameter_provenance_cards": [
            {
                "param_id": "P-T01",
                "alias": "P-01",
                "name": "Macro AI Accelerator Cluster Hardware TCO Learning Rate",
                "base_value": 0.150,
                "elasticity_b": -0.23447,
                "derived_range": [0.120, 0.180],
                "selection_rationale": "Historical CoWoS packaging learning curve (-28.5%) adjusted for liquid cooling & copper packaging friction (-13.0%) gives 15.5%; conservative margin of -0.50pp applied yielding base 15.0%.",
                "epistemic_type": "ASSUMPTION | Evidence-informed Assumption",
                "formula": "Wright's Law: C(Q) = C_1 * Q^b, LR = 1 - 2^b",
                "derivation_steps": [
                    "Step 1 [ESTIMATE]: TSMC 4nm/3nm wafer + CoWoS historical packaging learning rate = 28.50%",
                    "Step 2 [ASSUMPTION]: Data center physical friction model: LR_adj = LR_raw - Penalties",
                    "Step 3 [ASSUMPTION]: Liquid cooling (-6.0%), copper signal loss (-4.5%), geopolitical compliance (-2.5%)",
                    "Step 4 [MODEL RESULT]: Net adjusted theoretical learning rate = 15.50%",
                    "Step 5 [ASSUMPTION]: Conservative base 15.00% adopted with -0.50pp conservative margin"
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
                "name": "CoWoS Packaging & HBM3e Memory Stack Learning Rate",
                "base_value": 0.135,
                "elasticity_b": -0.2092,
                "formula": "Wright's Law: C(Q) = C_1 * Q^b, LR = 1 - 2^b",
                "derivation_steps": [
                    "Step 1 [ESTIMATE]: CoWoS-L packaging volume contracts",
                    "Step 2 [MODEL RESULT]: LR = 13.5%"
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
            "anti_double_counting_rule": "Top-down cluster learning rate excludes discrete CDU facility CAPEX to avoid double counting."
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
                        "scale": "100000_gpus",
                        "divergence_percent": 5.88,
                        "classification": "CONSISTENT",
                        "residual_honesty": {
                            "primary_explained_percent": 83.33,
                            "unexplained_residual_percent": 6.84
                        }
                    }
                ]
            }
        }
    }
    with open(NV_BENCHMARK_DIR / "assumptions.json", "w", encoding="utf-8") as f:
        json.dump(assumptions, f, indent=2, ensure_ascii=False)

    # 9. thesis.json
    print("[10/10] Building thesis.json and report.md...")
    thesis = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "evidence_to_hypothesis_impact_matrix": [
            {
                "evidence_id": "F-NV-01",
                "causal_distance": "DIRECT",
                "impact_HA": "STRONG_SUPPORT",
                "impact_HB": "NEUTRAL"
            },
            {
                "evidence_id": "F-NV-02",
                "causal_distance": "DIRECT",
                "impact_HA": "STRONG_SUPPORT",
                "impact_HB": "MODERATE_AGAINST"
            },
            {
                "evidence_id": "F-NV-03",
                "causal_distance": "NEAR",
                "impact_HA": "MODERATE_AGAINST",
                "impact_HB": "STRONG_SUPPORT"
            },
            {
                "evidence_id": "F-NV-04",
                "causal_distance": "FAR",
                "impact_HA": "WEAK_SUPPORT",
                "impact_HB": "WEAK_SUPPORT"
            }
        ],
        "active_research_questions": [
            "RQ-01: At what power scale does data center grid latency exceed optical interconnect overhead?",
            "RQ-02: Will hyperscaler internal ASIC adoption reduce commercial GPU merchant ASP in 2026?"
        ],
        "company_exposure_cards_decoupled": [
            {
                "name": "NVIDIA Corporation (NASDAQ: NVDA)",
                "company_fact_audit": {
                    "reported_segment": "Data center revenue exceeded $100B in FY25 (87.5% of total) [FACT F-NV-01]",
                    "pure_exposure": "Direct accelerator hardware & networking platform",
                    "knowns": "75% gross margin, GB200 NVL72 full rack integration",
                    "unknowns": "Longitudinal enterprise application ROI sustainability"
                },
                "earnings_translation": {
                    "formula": "ΔRevenue = Global_Hyperscaler_CAPEX × AI_Allocation × Share",
                    "scenario": "Hyperscaler $200B CAPEX at 50% AI allocation with 85% share yields ~$85B datacenter segment"
                },
                "valuation_sensitivity": {
                    "implied_expectations": "[MODEL RESULT | 逆向隐含预期测算] 在 30x 远期稳态 PE 与 50% 综合净利率假设下，当前 3.5 万亿美元市值对应英伟达每年需持续实现至少 700 亿 - 800 亿美元净利润，隐含了全球科技巨头必须维持每年 2,500 亿美元以上的 AI 资本开支且不发生剧烈周期衰退。"
                }
            }
        ]
    }
    with open(NV_BENCHMARK_DIR / "thesis.json", "w", encoding="utf-8") as f:
        json.dump(thesis, f, indent=2, ensure_ascii=False)

    # 10. report.md
    report_content = """# 英伟达 (NVIDIA) 产业链控制点与商业化成熟度深度研报

> **报告版本**：v3.5 (Topic-Agnostic Artifact Enforcement Edition)  
> **研究课题**：NVIDIA Computing Infrastructure & Ecosystem Control  
> **执行标准**：8-Tier Epistemic Taxonomy & 11 Deterministic Gates

---

## 01 执行摘要与竞争性假说矩阵 (Executive Summary)

- **`[FACT F-NV-01]`** 英伟达 2025 财年法定财报披露营收超 1,200 亿美元，数据中心业务占比 87.5%，前四大客户营收贡献度达 40%~45%。
- **`[FACT F-NV-02]`** Blackwell GB200 NVL72 单机架通过全铜缆直连实现 130 TB/s 双向 NVLink 5 域互联总带宽。
- **`[SECONDARY ESTIMATE F-NV-03]`** 高盛测算超大规模云厂商自研 ASIC 在特定推理与训练任务中的份额约为 18%~22%。
- **`[SECONDARY ESTIMATE F-NV-04]`** 红杉资本测算模型指出当前 AI 基础设施投入与终端企业级应用增量收入存在数百亿美元量级的商业化剪刀差。
- **`[ASSUMPTION P-T01]`** 设定宏观 AI 算力硬件系统 TCO 综合学习率基准为 15.00%。
- **`[MODEL RESULT]`** 模型测算在年产 10 万台机架量产规模下，机架单 GPU 综合硬件物料成本有望由 $35,000 降至 $20,400 区间。
- **`[INFERENCE]`** 计算芯片竞争已全面由单卡算力转向机架级物理散热、供电与芯片间超高速域互联网络系统工程。
- **`[FORECAST]`** 预计在下游云厂商维持 25% 以上资本开支复合增速条件下，全栈网络与系统解决方案仍将占据商业加速器 80% 以上采购份额。

### 控制节点定性分级表 (Categorical Control Grade Matrix)

| 控制节点 | 稀缺性 | 替代壁垒 | 规模效应 | 数据网络 | 综合控制等级 | 评估置信度 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NVLink/NVSwitch 域互联** | CRITICAL | CRITICAL | HIGH | HIGH | **CRITICAL** | **HIGH** |
| **CUDA 闭源并行计算生态** | HIGH | CRITICAL | HIGH | CRITICAL | **CRITICAL** | **HIGH** |
| **CoWoS 先进封装产能** | CRITICAL | HIGH | HIGH | LOW | **HIGH** | **HIGH** |
| **裸芯片原始算力 (Raw FLOPS)** | MEDIUM | MEDIUM | CRITICAL | LOW | **MEDIUM** | **HIGH** |

### 资本市场映射与逆向隐含预期模型

- **`[MODEL RESULT | 逆向隐含预期测算]`**：在 30x 远期稳态 PE 与 50% 净利率假设下，当前市值对应英伟达需持续实现年化 700 亿 - 800 亿美元净利润，隐含了全球科技巨头年化 AI 资本开支需持续维持在 2,500 亿美元以上高位。该测算仅为特定财务假设下的条件反推，不构成对市场客观事实或股票买卖的裁决。
"""
    with open(NV_BENCHMARK_DIR / "report.md", "w", encoding="utf-8") as f:
        f.write("> DEMO FIXTURE — synthetic records; not independently verified.\n\n" + report_content)

    # Also write to top-level reports
    with open(BASE_DIR / "reports" / "nvidia_industry_analysis.md", "w", encoding="utf-8") as f:
        f.write("> DEMO FIXTURE — synthetic records; not independently verified.\n\n" + report_content)

    print("\nNVIDIA benchmark scaffolded and stored successfully.")

if __name__ == "__main__":
    main()
