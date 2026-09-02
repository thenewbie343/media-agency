import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO)

os.environ["TEST_MODE"] = "hero"
os.environ["MOCK_LLM"] = "false"
os.environ["MOCK_QC"] = "false"
os.environ["VISION_STATUS"] = "AVAILABLE"  # Ensure we pass vision checks

def main():
    cfg = {
        "topic": "The Man Who Mastered 'Human Minds': Edward Bernays archival footage historical",
        "niche": "History",
        "genre": "documentary",
        "lang": "en",
        "duration_min": 1,
        "schedule": "00:00"
    }
    
    import pipeline
    pipeline.parse_input = lambda: cfg
    
    print("Running Edward Bernays Tier 4 Benchmark Test...")
    pipeline.run_pipeline_v52()
    print("Benchmark complete.")

if __name__ == "__main__":
    main()
