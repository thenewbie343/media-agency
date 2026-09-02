import os
import sys
import logging
from PIL import Image
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

from agents.asset_verifier import AssetVerifier, VisualRequirement

logging.basicConfig(level=logging.INFO)

def run():
    print("Creating test image...")
    img_path = "test_smoke_image.png"
    # Create RGBA image to test normalization
    img = Image.new('RGBA', (2000, 2000), color=(255, 0, 0, 128))
    img.save(img_path)

    verifier = AssetVerifier()
    verifier.gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
    if not verifier.gemini_key:
        print("No GEMINI_API_KEY. Cannot run full smoke test.")
        return

    req = VisualRequirement(
        shot_id="smoke_01",
        subject_entity="Red box",
        event="Testing VLM",
        time_period="Modern",
        date_range="2020s",
        location="Studio",
        required_objects=[],
        forbidden_objects=[]
    )
    
    print("Testing normalization and VLM call...")
    try:
        res = verifier._call_vlm_observer(img_path, req)
        print("SUCCESS! VLM returned:")
        print(res)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == '__main__':
    run()
