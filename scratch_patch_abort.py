import re
with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"script, research, stats = run_documentary_pipeline\(cfg\)"
replacement = """script, research, stats = run_documentary_pipeline(cfg)
            if stats.get("final_status") in ["REJECTED", "REJECTED_NO_REPAIR"]:
                log.error("🛑 Master script rejected by Script QC. Halting pipeline to prevent downstream failure cascade.")
                return False"""

new_content, count = re.subn(pattern, replacement, content)
if count > 0:
    with open("pipeline.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patched!")
else:
    print("Target not found.")
