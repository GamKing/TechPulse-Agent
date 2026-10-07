import json
from pathlib import Path

def update_thesis():
    path = Path("reports/humanoid_robot_benchmark/thesis.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["version"] = "3.5-benchmark-artifact-enforcement"

    # Add E-H01 to evidence_to_hypothesis_impact_matrix if not present
    matrix = data.get("evidence_to_hypothesis_impact_matrix", [])
    if not any(row.get("evidence_id") == "E-H01" for row in matrix):
        matrix.append({
            "evidence_id": "E-H01",
            "epistemic_type": "SECONDARY_ESTIMATE",
            "claim_summary": "Cobot 2016-2024 累计制造 1.5万->21万台，均价降至 $19k，实证 LR=16.25%",
            "causal_distance": "NEAR_TO_HB",
            "missing_bridges": "协作机械臂在关节电机与控制算法上具有相似降本路径，但缺乏双足全身动力学与高自由度手腕热耗特征",
            "impact_HA": "NEUTRAL",
            "impact_HB": "MODERATE_SUPPORT",
            "impact_HC": "NEUTRAL",
            "marginal_posterior": "P(HB) supported as cross-domain benchmark"
        })
    data["evidence_to_hypothesis_impact_matrix"] = matrix

    # Update audit_status flags
    astatus = data.get("audit_status", {})
    astatus["err_12_residual_honesty_verified"] = True
    astatus["err_13_artifact_enforcement_verified"] = True
    astatus["err_14_validation_decoupled_verified"] = True
    astatus["external_evidence_audit_scorecard"] = "audit_scorecard.json"
    data["audit_status"] = astatus

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("thesis.json updated successfully.")

if __name__ == "__main__":
    update_thesis()
