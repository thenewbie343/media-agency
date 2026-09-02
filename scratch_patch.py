with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """                record = {
                    "shot_id": shot_id,
                    "required_visual": req.get("subject_entity") or req.get("event") or shot.get("visual_description", "")[:60],
                    "verdict": verdict,
                    "rejection_reasons": v_res.get("rejection_reasons", [])
                }
                audit_records.append(record)"""

replacement = """                record = {
                    "shot_id": shot_id,
                    "required_visual": req.get("subject_entity") or req.get("event") or shot.get("visual_description", "")[:60],
                    "verdict": verdict,
                    "verifier_provider": v_res.get("verifier_provider", "UNKNOWN"),
                    "verifier_status": v_res.get("verifier_status", "UNKNOWN"),
                    "unverified": v_res.get("unverified", False),
                    "rejection_reasons": v_res.get("rejection_reasons", [])
                }
                
                # Explicitly log unverified states for debugging
                if record["unverified"]:
                    from agents.schema import log
                    log.warning(f"Shot {shot_id}: UNVERIFIED. Provider: {record['verifier_provider']}, Status: {record['verifier_status']}")
                    
                audit_records.append(record)"""

if target in content:
    content = content.replace(target, replacement)
    with open("pipeline.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched!")
else:
    print("Target not found.")
