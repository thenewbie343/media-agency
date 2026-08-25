import os
import sys
from pipeline import run_pipeline_v52

# Fake inputs via env vars
os.environ["TEST_MODE"] = "true"
os.environ["SCRIPT_INPUT"] = ""
os.environ["TOPIC"] = "The truth of vijay mallaya"
os.environ["GENRE"] = "documentary"
os.environ["LANG"] = "hindi"
os.environ["DURATION"] = "4"

print("Running Pipeline V5.2 with V3 Visual Intelligence (TEST_MODE=true)...")
run_pipeline_v52()
print("Done!")
