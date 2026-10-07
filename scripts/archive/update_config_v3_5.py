import json
from pathlib import Path

def update_config():
    path = Path("config/pipeline_config.json")
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    tier3 = cfg["tiers"]["tier_3_deterministic_judge"]["scoring_policy"]
    
    # Add GATE_ARTIFACT_ENFORCEMENT if not present
    if "GATE_ARTIFACT_ENFORCEMENT" not in tier3["high_priority_gates"]:
        tier3["high_priority_gates"].append("GATE_ARTIFACT_ENFORCEMENT")

    tier3["artifact_enforcement_policy"] = {
        "required_artifacts": [
            "parameter_registry.json",
            "validation_criteria.json",
            "holdout_registry.json",
            "model_run_topdown.json",
            "model_run_bottomup.json",
            "validation_run.json",
            "audit_log.jsonl",
            "evidence.jsonl"
        ],
        "require_cryptographic_hashes": True,
        "require_firewall_permission_check": True,
        "require_decoupled_verdict": True
    }

    tier3["residual_honesty_policy"] = {
        "forbid_100_percent_artificial_balance": True,
        "require_unexplained_residual_acknowledged": True,
        "min_unexplained_residual_pct": 3.0,
        "max_unexplained_residual_pct": 15.0
    }

    forbidden = tier3.get("forbidden_subjective_valuation_terms", [])
    for term in ["已提前预支了", "市场已经预支了"]:
        if term not in forbidden:
            forbidden.append(term)
    tier3["forbidden_subjective_valuation_terms"] = forbidden

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    print("pipeline_config.json updated successfully.")

if __name__ == "__main__":
    update_config()
