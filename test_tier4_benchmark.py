import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from pipeline import parse_input, run_pipeline_v52

logging.basicConfig(level=logging.INFO)

# Override environment for testing
os.environ["TEST_MODE"] = "hero"
os.environ["MOCK_LLM"] = "false"  # Ensure we actually test

def main():
    cfg = {
        "topic": "The Computer Error That Almost Started World War 3",
        "niche": "Technology History",
        "genre": "documentary",
        "lang": "en",
        "duration_min": 2,
        "schedule": "00:00"
    }
    
    # We will inject this into sys.argv so parse_input() picks it up if it uses argparse,
    # or we can mock parse_input.
    
    # Actually, pipeline.py might read sys.argv. Let's just mock it.
    import pipeline
    pipeline.parse_input = lambda: cfg
    
    # Let's run the documentary pipeline
    print("Running Tier 4 Benchmark Test...")
    run_pipeline_v52()
    print("Benchmark complete.")

if __name__ == "__main__":
    main()
