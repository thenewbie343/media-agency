# E2E Test Infra: Visual Storytelling Engine & Story Planner

## Test Philosophy
- Opaque-box and requirement-driven testing based on `ORIGINAL_REQUEST.md`.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial Testing + Real-World Workload Testing.
- Guarantees: 100% offline determinism via fast mock fixtures for LLMs, TTS, and video rendering, supplemented by live component validation.

## Feature Inventory & Test Tier Mapping
| # | Feature | Source (Requirement) | Tier 1 (Coverage) | Tier 2 (Boundaries) | Tier 3 (Combinations) | Tier 4 (Scenarios) |
|---|---------|----------------------|:-----------------:|:-------------------:|:---------------------:|:------------------:|
| F1 | Dependency Mapping & Interface Safety | R1 | 5 | 5 | ✓ | ✓ |
| F2 | Visual Story Planner Dynamic Splitting | R2 | 5 | 5 | ✓ | ✓ |
| F3 | Visual Job & Asset Provenance Diversity | R3 | 5 | 5 | ✓ | ✓ |
| F4 | Camera Fatigue & Anti-Fatigue Memory | R4 | 5 | 5 | ✓ | ✓ |
| F5 | Duration Planning & Ratio Rescaling | R5 | 5 | 5 | ✓ | ✓ |
| F6 | Semantic Cut Reasons | R5 | 5 | 5 | ✓ | ✓ |
| F7 | Pipeline Asset Routing & Fallback Waterfall | R5, R7 | 5 | 5 | ✓ | ✓ |
| F8 | 2.5D Parallax Subject Cutouts with Alpha Blur | R7, AC | 5 | 5 | ✓ | ✓ |
| F9 | Pre-Render Asset & SFX Auditing | R7, AC | 5 | 5 | ✓ | ✓ |
| F10 | Remotion Multi-Layer Compositing | R6 | 5 | 5 | ✓ | ✓ |
| F11 | TypeScript Schema Synchronization | R6, AC | 5 | 5 | ✓ | ✓ |
| F12 | Fallback Text-Wrapping & Zero-Overflow | R6, AC | 5 | 5 | ✓ | ✓ |
| F13 | Backward Compatibility (Legacy/Flat/Single) | AC | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Framework: `pytest 8.4.1` on Python 3.12.10
- Configuration: `pytest.ini` at project root with custom markers (`unit`, `integration`, `e2e`, `tier1`, `tier2`, `tier3`, `tier4`, `tier5`)
- Test Suite Location: `tests/`
  - `tests/conftest.py`: Mock fixtures for LLM responses, TTS durations, video generators, and sample manifests.
  - `tests/test_tier1_features.py`: Schema validation, dynamic beat-to-shot splitting, visual jobs, anti-fatigue memory, duration ratio normalization, and backward compatibility.
  - `tests/test_tier2_boundaries.py`: Micro-beats (<2s), mega-beats (>20s), schema self-repair, null cinematography defaults, asset 404 audit, and SFX safety.
  - `tests/test_tier3_combinations.py`: 16 Visual Jobs x 8 Provenances x 9 Fallbacks matrix, multi-layer Remotion compositing, agent closed-loop repair, and polymorphic input ingestion.
  - `tests/test_tier4_scenarios.py`: Full 3-Act documentary simulation ("The Fall of Nokia"), 30s high-tempo crisis hook, archival deep-dive, and total AI video outage fallback.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | "The Fall of Nokia" Full 3-Act Documentary Simulation | F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F13 | High |
| 2 | High-Tempo 30-Second Crisis Hook | F2, F3, F4, F5, F6, F10, F12 | Medium |
| 3 | Historical Archival Dossier & Classified File Deep-Dive | F3, F7, F9, F10, F11, F12 | Medium |
| 4 | Total AI Video Outage & Semantic Fallback Resilience | F7, F9, F10, F12, F13 | High |

## Coverage Thresholds
- Tier 1: $\ge 5$ test cases per feature ($\ge 65$ tests total)
- Tier 2: $\ge 5$ boundary/edge test cases per feature ($\ge 65$ tests total)
- Tier 3: Pairwise and combinatorial interaction tests ($\ge 15$ test cases)
- Tier 4: $\ge 4$ realistic full-workload documentary scenarios
- **Total Minimum Target**: $>145$ verified test assertions
