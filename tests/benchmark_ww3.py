import os
import json
import logging
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.adaptive_critic import GeminiQuotaManager, ReviewMode, Level1_SemanticCritic, Level2_SelectiveGemini

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def run_benchmark():
    print("============================================================")
    print(" BENCHMARK: The Computer Error That Almost Started WW3")
    print("============================================================\n")

    manager = GeminiQuotaManager(mode=ReviewMode.BALANCED_REVIEW)

    # Mock shots: (name, narrative_intent, mock_confidence, mock_anachronism)
    shots = [
        ("s001_siren", "HOOK", 0.95, 0.0), # High priority, high conf -> Might still call Gemini because HOOK > 0.8
        ("s002_radar", "SETUP", 0.92, 0.0), # Low priority, high conf -> Skip Gemini
        ("s003_petrov", "EVIDENCE", 0.80, 0.0), # Evidence, med conf -> Gemini
        ("s004_bunker_pan", "TRANSITION", 0.98, 0.0), # Transition, high conf -> Skip Gemini
        ("s005_satellite", "SETUP", 0.91, 0.0), # Skip
        ("s006_screen_glitch", "REVEAL", 0.60, 0.0), # Reveal, low conf -> Gemini
        ("s007_sweat", "CLIMAX", 0.85, 0.0), # Climax -> Gemini
        ("s008_phone", "TRANSITION", 0.96, 0.0), # Skip
        ("s009_missile_launch", "CLIMAX", 0.90, 0.0), # Climax -> Gemini
        ("s010_empty_sky", "PAYOFF", 0.95, 0.0) # Payoff -> Gemini
    ]

    print(f"Total Shots to Process: {len(shots)}")
    print(f"Starting Mode: {manager.mode.value}\n")

    for name, intent, conf, anachronism in shots:
        print(f"Processing Shot: {name} (Intent: {intent})")
        
        # Level 1
        obs = {
            "entity_confidence": conf,
            "event_confidence": conf,
            "date_confidence": conf,
            "anachronism_score": anachronism
        }
        semantic_conf, local_decision = Level1_SemanticCritic.evaluate(obs, "HISTORICAL")
        
        # Priority mapping
        priority = 0.3 # default transition
        if intent in ["HOOK", "CLIMAX", "PAYOFF", "REVEAL", "EVIDENCE"]:
            priority = 0.9
            
        # Level 2
        needs_gemini = Level2_SelectiveGemini.evaluate(manager, semantic_conf, priority)
        
        if needs_gemini:
            # Simulate Gemini Call
            print(f"  -> Triggering Gemini Vision API (Priority: {priority}, Local Conf: {semantic_conf:.2f})")
            manager.record_call(True)
        else:
            print(f"  -> SKIPPING Gemini (Local Semantic PASS. Priority: {priority}, Local Conf: {semantic_conf:.2f})")
            manager.record_avoided()

    print("\n============================================================")
    print(" BENCHMARK REPORT")
    print("============================================================")
    print(f"Final Mode: {manager.mode.value}")
    print(f"Total Shots: {len(shots)}")
    print(f"Gemini Calls Used: {manager.calls_used}")
    print(f"Gemini Calls Avoided: {manager.calls_avoided}")
    
    # Assertions for the test
    assert manager.calls_avoided > 0, "Test failed: No calls were avoided!"
    assert manager.calls_used < len(shots), "Test failed: Used Gemini on every shot!"
    
    print("============================================================")
    print(" PASS: Free-Tier Safe Architecture Verified.")
    print("============================================================")

    # Now test Failure Degradation
    print("\n\n--- TESTING GEMINI FAILURE DEGRADATION ---")
    manager_fail = GeminiQuotaManager(mode=ReviewMode.BALANCED_REVIEW)
    manager_fail.record_call(False) # 1 fail
    manager_fail.record_call(False) # 2 fail
    manager_fail.record_call(False) # 3 fail (should downgrade)
    
    assert manager_fail.mode == ReviewMode.OFFLINE_REVIEW, "Test failed: Did not downgrade to offline mode!"
    assert manager_fail.can_call(0.99) == False, "Test failed: Still allowing calls in OFFLINE mode!"
    print(" PASS: Quota degradation is functional.")

if __name__ == '__main__':
    run_benchmark()
