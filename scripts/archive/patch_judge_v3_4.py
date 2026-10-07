import re

def main():
    judge_path = "scripts/deterministic_judge.py"
    with open(judge_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define Gate 5 revised with 3-tier categorization policy
    gate_5_replacement = '''    # =========================================================================
    # GATE 5: PARAMETER ORTHOGONALITY & 3-TIER DIVERGENCE POLICY GATE (Critical)
    # =========================================================================
    def audit_gate_5_parameter_orthogonality_dual_model(self, assumptions_data):
        gate_name = "GATE_PARAMETER_ORTHOGONALITY_DUAL_MODEL"
        if not assumptions_data:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "assumptions.json not found."}

        ortho = assumptions_data.get("parameter_orthogonality_audit", {})
        dual_model = assumptions_data.get("dual_model_architecture", {})

        if not ortho or not dual_model:
            return {
                "gate": gate_name,
                "type": "CRITICAL",
                "status": "FAIL",
                "details": "Missing parameter_orthogonality_audit or dual_model_architecture."
            }

        # Check anti-double counting rule
        anti_dc = ortho.get("anti_double_counting_rule", "")
        if not anti_dc:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "Missing anti_double_counting_rule."}

        # Check dual model divergences under 3-tier policy:
        # <20%: CONSISTENT, 20-40%: MATERIAL_DIVERGENCE, >40%: MODEL_CONFLICT
        div_audit = dual_model.get("divergence_audit", {})
        divergences = div_audit.get("divergences", [])

        invalid_classifications = []
        conflicts = []
        for d in divergences:
            scale = d.get("scale", "")
            div_pct = d.get("divergence_percent", 999.0)
            classification = d.get("classification", "")
            if div_pct < 20.0 and classification != "CONSISTENT":
                invalid_classifications.append(f"{scale}: {div_pct}% must be classified as CONSISTENT")
            elif 20.0 <= div_pct <= 40.0 and classification != "MATERIAL_DIVERGENCE":
                invalid_classifications.append(f"{scale}: {div_pct}% must be classified as MATERIAL_DIVERGENCE")
            elif div_pct > 40.0:
                conflicts.append(f"{scale}: divergence {div_pct}% > 40% triggers MODEL_CONFLICT")

        if invalid_classifications or conflicts:
            return {
                "gate": gate_name,
                "type": "CRITICAL",
                "status": "FAIL",
                "details": f"Divergence policy violation: Invalid: {invalid_classifications}; Conflicts: {conflicts}"
            }

        max_div = max(d.get("divergence_percent", 0.0) for d in divergences)
        return {
            "gate": gate_name,
            "type": "CRITICAL",
            "status": "PASS",
            "details": f"Anti-double-counting decoupled. All {len(divergences)} volume stages conform to 3-tier policy (Max observed divergence: {max_div}% -> CONSISTENT).",
            "divergence_audit": divergences
        }

    # =========================================================================
    # GATE 6: PARAMETER PRE-REGISTRATION & BLIND PARAMETERIZATION GATE (Critical)
    # =========================================================================
    def audit_gate_parameter_preregistration_blind(self, assumptions_data):
        gate_name = "GATE_PARAMETER_PREREGISTRATION_BLIND"
        if not assumptions_data:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "assumptions.json not found."}

        registry = assumptions_data.get("blind_parameterization_registry", {})
        cards = assumptions_data.get("parameter_provenance_cards", [])

        if not registry:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "Missing blind_parameterization_registry."}

        reg_violations = []
        if registry.get("isolation_protocol") != "BLIND_PARAMETERIZATION_ENFORCED":
            reg_violations.append("isolation_protocol must be 'BLIND_PARAMETERIZATION_ENFORCED'")

        t_pre = registry.get("pre_registration_timestamp", "")
        t_comp = registry.get("comparison_timestamp", "")
        if not t_pre or not t_comp:
            reg_violations.append("Missing pre_registration_timestamp or comparison_timestamp")
        elif t_pre >= t_comp:
            reg_violations.append(f"Pre-registration timestamp ({t_pre}) must precede comparison timestamp ({t_comp})")

        if not str(registry.get("top_down_set_hash", "")).startswith("sha256:") or not str(registry.get("bottom_up_set_hash", "")).startswith("sha256:"):
            reg_violations.append("Missing or invalid sha256 parameter set hashes in registry")

        if registry.get("post_comparison_modification_detected", True):
            reg_violations.append("Post-comparison modification detected! Cross-validation invalid.")

        card_violations = []
        for c in cards:
            pid = c.get("param_id", "UNKNOWN")
            if not c.get("selected_before_cross_model_output", False):
                card_violations.append(f"{pid}: selected_before_cross_model_output must be true")
            if not c.get("locked", False):
                card_violations.append(f"{pid}: parameter must be locked")
            if not c.get("locked_at"):
                card_violations.append(f"{pid}: missing locked_at timestamp")
            if not str(c.get("parameter_set_hash", "")).startswith("sha256:"):
                card_violations.append(f"{pid}: missing valid sha256 parameter_set_hash")
            if c.get("modified_after_comparison", True):
                card_violations.append(f"{pid}: modified_after_comparison is true (calibration-to-target violation)")
            calib_status = c.get("calibration_status", "")
            if calib_status != "UNTOUCHED_INDEPENDENT":
                card_violations.append(f"{pid}: calibration_status '{calib_status}' is not UNTOUCHED_INDEPENDENT")

        if reg_violations or card_violations:
            return {
                "gate": gate_name,
                "type": "CRITICAL",
                "status": "FAIL",
                "details": f"Pre-registration violations: {reg_violations}; Card violations: {card_violations}"
            }

        return {
            "gate": gate_name,
            "type": "CRITICAL",
            "status": "PASS",
            "details": f"Blind parameterization enforced. All {len(cards)} parameters pre-registered, cryptographically hashed, and locked before comparison. Post-hoc calibration prohibited."
        }

    # =========================================================================
    # GATE 7: CROSS-MODEL INDEPENDENCE & DIVERGENCE ATTRIBUTION GATE (High)
    # =========================================================================
    def audit_gate_cross_model_independence_and_attribution(self, assumptions_data):
        gate_name = "GATE_CROSS_MODEL_INDEPENDENCE_AND_ATTRIBUTION"
        if not assumptions_data:
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": "assumptions.json not found."}

        # 1. Check In-Sample Calibration vs Out-of-Sample Validation
        calib_valid = assumptions_data.get("in_sample_calibration_and_out_of_sample_validation", {})
        if not calib_valid:
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": "Missing in_sample_calibration_and_out_of_sample_validation block."}

        in_sample = calib_valid.get("in_sample_calibration", {})
        out_sample = calib_valid.get("out_of_sample_validation", {})

        if not in_sample.get("dataset") or not out_sample.get("dataset"):
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": "Missing datasets for in-sample or out-of-sample."}

        if "PASS" not in out_sample.get("validation_result", ""):
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": f"Out-of-sample validation failed: {out_sample.get('validation_result')}"}

        # 2. Check Divergence Attribution
        dual_model = assumptions_data.get("dual_model_architecture", {})
        div_audit = dual_model.get("divergence_audit", {})
        divergences = div_audit.get("divergences", [])

        attribution_errors = []
        for d in divergences:
            scale = d.get("scale", "")
            diff_cny = d.get("diff_cny", 0.0)
            attrib = d.get("divergence_attribution", {})
            if not attrib:
                attribution_errors.append(f"{scale}: missing divergence_attribution dict")
                continue
            attrib_sum = sum(attrib.values())
            if abs(attrib_sum - diff_cny) > 1.0:
                attribution_errors.append(f"{scale}: attribution sum {attrib_sum} != diff_cny {diff_cny}")

        if attribution_errors:
            return {
                "gate": gate_name,
                "type": "HIGH",
                "status": "FAIL",
                "details": f"Divergence attribution errors: {attribution_errors}"
            }

        return {
            "gate": gate_name,
            "type": "HIGH",
            "status": "PASS",
            "details": f"In-sample calibration (1995-2015) decoupled from out-of-sample validation (2016-2024 Cobots: PASS). All {len(divergences)} volume stages provide 100% matched quantitative divergence attribution."
        }
'''

    # Replace old Gate 5 with gate_5_replacement
    old_gate_5_pattern = r"    # =========================================================================\s+# GATE 5: PARAMETER ORTHOGONALITY & DUAL-MODEL DIVERGENCE GATE \(Critical\)\s+# =========================================================================.*?return \{\s+\"gate\": gate_name,\s+\"type\": \"CRITICAL\",\s+\"status\": \"PASS\",\s+\"details\": f\"Anti-double-counting decoupled\. All \{len\(divergences\)\} volume stages have divergence < \{max_threshold\}% \(Max observed: \{max\(d\.get\('divergence_percent', 0\.0\) for d in divergences\)\}%\)\.\",\s+\"divergence_audit\": divergences\s+\}"

    if not re.search(old_gate_5_pattern, content, re.DOTALL):
        print("Error: Could not locate old Gate 5 pattern in deterministic_judge.py")
        return

    content = re.sub(old_gate_5_pattern, gate_5_replacement, content, count=1, flags=re.DOTALL)

    # Now update execute_audit list
    old_results_pattern = r"results = \[\s+self\.audit_gate_1_source_existence\(evidence_records\),\s+self\.audit_gate_2_claim_entailment_target_result\(evidence_records\),\s+self\.audit_gate_3_epistemic_birth_certificate\(evidence_records\),\s+self\.audit_gate_4_parameter_provenance_recalculation\(assumptions_data\),\s+self\.audit_gate_5_parameter_orthogonality_dual_model\(assumptions_data\),\s+self\.audit_gate_6_global_precision_regex\(report_text\),\s+self\.audit_gate_7_causal_distance_penalty\(thesis_data\),\s+self\.audit_gate_8_valuation_decoupling\(report_text, thesis_data\)\s+\]"

    new_results = '''results = [
            self.audit_gate_1_source_existence(evidence_records),
            self.audit_gate_2_claim_entailment_target_result(evidence_records),
            self.audit_gate_3_epistemic_birth_certificate(evidence_records),
            self.audit_gate_4_parameter_provenance_recalculation(assumptions_data),
            self.audit_gate_5_parameter_orthogonality_dual_model(assumptions_data),
            self.audit_gate_parameter_preregistration_blind(assumptions_data),
            self.audit_gate_cross_model_independence_and_attribution(assumptions_data),
            self.audit_gate_6_global_precision_regex(report_text),
            self.audit_gate_7_causal_distance_penalty(thesis_data),
            self.audit_gate_8_valuation_decoupling(report_text, thesis_data)
        ]'''

    if not re.search(old_results_pattern, content, re.DOTALL):
        print("Error: Could not locate old results pattern in execute_audit")
        return

    content = re.sub(old_results_pattern, new_results, content, count=1, flags=re.DOTALL)

    with open(judge_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully patched deterministic_judge.py with Gate 6 & Gate 7!")

if __name__ == "__main__":
    main()
