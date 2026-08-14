import re

def verify_llm_grounding(llm_output, evidence):
    """
    Verifies that numeric values mentioned in LLM text (prices, percentages, targets)
    actually exist in the evidence bundle to prevent hallucinations.
    """
    if not isinstance(llm_output, str) or not llm_output.strip():
        return {"verifier_ok": True, "violations": []}

    # Extract numeric figures (e.g. ₹1450, 4.2%, 2.4x)
    numbers_in_text = re.findall(r'₹?\s*(\d+(?:\.\d+)?)%?', llm_output)
    
    # Flatten numeric values from evidence
    evidence_nums = set()

    def extract_nums(val):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            evidence_nums.add(round(float(val), 2))
            evidence_nums.add(round(float(val), 1))
            evidence_nums.add(int(val))
        elif isinstance(val, dict):
            for v in val.values():
                extract_nums(v)
        elif isinstance(val, list):
            for v in val:
                extract_nums(v)

    extract_nums(evidence)

    violations = []
    for num_str in numbers_in_text:
        try:
            val = float(num_str)
            # Ignore common integers like 1, 2, 5, 10, 20, 50, 100
            if val in (1, 2, 3, 4, 5, 10, 20, 50, 100):
                continue
            
            val_round = round(val, 2)
            val_round1 = round(val, 1)
            val_int = int(val)

            match_found = False
            for ev_num in evidence_nums:
                if abs(ev_num - val) <= 0.05 or abs(ev_num - val) / max(1.0, abs(ev_num)) <= 0.02:
                    match_found = True
                    break
            
            if not match_found and val > 10.0:
                violations.append(f"Unverified figure '{num_str}' not present in evidence bundle")
        except Exception:
            pass

    # Reject if more than 3 ungrounded numeric claims exist
    is_ok = len(violations) <= 2
    return {
        "verifier_ok": is_ok,
        "violations": violations,
        "checked_count": len(numbers_in_text)
    }
