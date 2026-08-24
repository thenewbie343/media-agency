import os
import json
import re
import logging
import time

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None

log = logging.getLogger("agency")

class BaseAgent:
    FORCE_GROQ = False

    def __init__(self, model_name="gemini-3.1-flash-lite"):
        self.model_name = model_name
        self.model = None
        
        # Setup Gemini
        gemini_key = os.environ.get("GEMINI_KEY", "")
        if not gemini_key:
            log.warning("GEMINI_KEY not found in environment. Agent calls will fail or use mock fallback.")
        else:
            if genai:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )

    def _get_mock_fallback(self, prompt, system_prompt, require_json):
        cls_name = self.__class__.__name__
        log.warning(f"[{cls_name}] Operating without API keys. Returning mock data for test execution.")
        
        research_pkg = {
            "topic": "The Fall of Nokia",
            "central_question": "How did the uncontested titan of mobile telecommunications collapse from within in less than five years?",
            "documentary_thesis": "Nokia's downfall was not a failure of hardware engineering, but an organizational culture paralyzed by internal fear and architectural blindness to software ecosystems.",
            "central_contradiction": "Nokia spent billions on R&D and invented smartphone touchscreen prototypes years before Apple, yet released products that destroyed its own market share.",
            "audience_initial_belief": "Nokia simply missed the smartphone trend because it was slow and old-fashioned.",
            "what_the_audience_thinks_is_true": "Apple out-innovated Nokia overnight with the iPhone.",
            "what_is_actually_more_complicated": "Nokia had working touchscreen smartphones and an app store before Apple, but middle management hid software defects from top executives due to a climate of fear.",
            "protagonist_or_human_anchor": "Jorma Ollila and Stephen Elop, alongside disillusioned Symbian OS software architects.",
            "antagonistic_force_or_system": "The bureaucratic matrix structure and the collapsing Symbian software codebase.",
            "stakes": "Loss of a $250 billion market capitalization and national economic crisis for Finland.",
            "historical_context": "The mid-2000s transition from hardware-differentiated feature phones to software-driven smartphone ecosystems.",
            "turning_points": [
                {
                    "timeframe": "January 2007",
                    "event": "Steve Jobs announces the iPhone at Macworld.",
                    "consequence": "Exposes the deep architectural inadequacy of Nokia's Symbian operating system."
                },
                {
                    "timeframe": "February 2011",
                    "event": "CEO Stephen Elop issues the famous 'Burning Platform' memo.",
                    "consequence": "Devastates current Symbian sales before Windows Phone devices are ready."
                },
                {
                    "timeframe": "September 2013",
                    "event": "Microsoft acquires Nokia's mobile phone business for $7.2 billion.",
                    "consequence": "Marks the final end of Nokia as an independent mobile phone manufacturer."
                }
            ],
            "major_reveals": [
                {
                    "phase": "FIRST_DISCOVERY",
                    "revelation": "Nokia engineers built a touchscreen phone prototype in 2004, but executives shelved it.",
                    "evidence_backing": "Internal Nokia research archives and patent filings."
                },
                {
                    "phase": "REVELATION",
                    "revelation": "Symbian OS required 57 steps to add a single feature to the camera app compared to 3 lines of code on iOS.",
                    "evidence_backing": "Former Nokia software developer testimonies and code audit logs."
                },
                {
                    "phase": "DEEPER_REVELATION",
                    "revelation": "Management culture punished realistic progress reports, causing middle managers to lie about software completion dates.",
                    "evidence_backing": "INSEAD organizational case study and executive email correspondence."
                },
                {
                    "phase": "FINAL_CONTRADICTION",
                    "revelation": "Nokia held the patents that modern smartphones rely on, earning royalties from the very companies that destroyed its phone business.",
                    "evidence_backing": "Global telecommunications patent portfolio licensing agreements."
                },
                {
                    "phase": "PAYOFF",
                    "revelation": "Hardware dominance is illusory when the paradigm shifts from devices to software platforms.",
                    "evidence_backing": "Global smartphone operating system market share data 2007-2015."
                }
            ],
            "final_payoff": "The tragic irony that Nokia built the foundation of the modern mobile world, only to become its most famous casualty.",
            "evidence_items": [
                {
                    "title": "The Burning Platform Memo",
                    "evidence_type": "memo",
                    "description": "Stephen Elop's internal memo comparing Nokia's market position to a worker standing on a burning oil platform.",
                    "source_reference": "Nokia Internal Communications / Wall Street Journal, Feb 2011",
                    "visual_cue": "Classified memo document with bold typography and redaction highlights"
                },
                {
                    "title": "Symbian Codebase Complexity Audit",
                    "evidence_type": "document",
                    "description": "Software architecture diagram showing tangled interdependencies across millions of lines of legacy C++ code.",
                    "source_reference": "Nokia Research Center Technical Report",
                    "visual_cue": "Technical architectural diagram with warning indicators and red error loops"
                },
                {
                    "title": "2004 Touchscreen Prototype Patent",
                    "evidence_type": "court_filing",
                    "description": "Nokia design patent showing a capacitive touchscreen tablet phone predating the iPhone by 3 years.",
                    "source_reference": "European Patent Office Filing EP1584982",
                    "visual_cue": "Archival patent blueprint with engineering annotations"
                }
            ],
            "people": [
                {
                    "name": "Jorma Ollila",
                    "role": "CEO & Chairman (1992-2006)",
                    "significance": "Built Nokia into the world's dominant mobile phone powerhouse.",
                    "visual_description": "Finnish executive in dark tailored suit, commanding boardrooms."
                },
                {
                    "name": "Stephen Elop",
                    "role": "CEO (2010-2013)",
                    "significance": "Authored the Burning Platform memo and steered Nokia to Windows Phone.",
                    "visual_description": "Former Microsoft executive, intense presentation delivery on stage."
                }
            ],
            "locations": [
                "Espoo, Finland (Nokia Headquarters)",
                "Salò, Finland (Flagship manufacturing plant)",
                "Cupertino, California (Apple HQ)",
                "Redmond, Washington (Microsoft HQ)"
            ],
            "physical_objects": [
                "Nokia 3310 indestructible feature phone",
                "Nokia N95 dual-slider multimedia phone",
                "Internal hardware prototype boards",
                "The physical printout of the Burning Platform memo"
            ],
            "numbers": [
                {
                    "raw_value": "49.4%",
                    "metric_label": "Global Smartphone Market Share in 2007",
                    "visual_treatment": "typographic_impact",
                    "editorial_context": "Peak market dominance right before the launch of the iPhone."
                },
                {
                    "raw_value": "$250,000,000,000",
                    "metric_label": "Market Value Lost (2007-2012)",
                    "visual_treatment": "odometer_counter",
                    "editorial_context": "One of the steepest collapses in corporate market history."
                },
                {
                    "raw_value": "$7.2 Billion",
                    "metric_label": "Microsoft Acquisition Price",
                    "visual_treatment": "split_comparison",
                    "editorial_context": "Purchased for a fraction of its former peak value."
                }
            ],
            "dates": [
                "January 9, 2007",
                "October 22, 2008",
                "February 11, 2011",
                "September 3, 2013"
            ],
            "archival_opportunities": [
                "Vintage Finnish mobile assembly line footage (1990s)",
                "Nokia N-Gage and N95 launch keynote events",
                "Jorma Ollila address at World Economic Forum",
                "Stock trading floor reactions during Nokia downgrade"
            ],
            "reconstruction_opportunities": [
                "Cinematic recreation of late-night executive meetings in Espoo",
                "Software engineers staring at crashing Symbian build logs",
                "Solitary figure reading the Burning Platform memo at dawn"
            ],
            "motion_graphic_opportunities": [
                "Global mobile market share pie chart collapsing from 50% to 3%",
                "Symbian vs iOS architecture dependency complexity comparison",
                "Interactive timeline map of Nokia headquarters to Redmond"
            ],
            "visual_motifs": [
                "The classic Nokia blue corporate banner",
                "The blue connecting hands animation",
                "Cracked glass screens and discarded plastic keypad housings",
                "Fluorescent-lit empty Finnish corridors at dusk"
            ],
            "ending_image_opportunity": "A lone, pristine Nokia 3310 lying silently on an abandoned testing bench while modern smartphone reflections sweep across the background window."
        }

        if cls_name == "ResearcherAgent":
            return research_pkg
        elif cls_name == "HeadWriterAgent":
            return {
                "title": "The Fall of Nokia: The Empire That Blinded Itself",
                "documentary_thesis": "Nokia's downfall was an internal collapse caused by architectural software debt and corporate fear.",
                "hook_strategy": {
                    "hook_type": "CONTRADICTION",
                    "target_duration_seconds": 25.0,
                    "anomaly_description": "In 2007, Nokia sold 1 in every 2 smartphones on Earth. Five years later, its market value evaporated by $250 billion.",
                    "withholding_element": "Withhold early company history; open immediately on the shocking collapse metric and secret shelved prototype.",
                    "opening_visual_cue": "Extreme macro close-up of a cracked Nokia blue logo screen glitching out."
                },
                "macro_phases": [
                    {"phase": "HOOK", "scene_number": 1, "description": "The $250 Billion Evaporation - Shocking collapse anomaly", "mini_arc_phase": "SETUP"},
                    {"phase": "CENTRAL_QUESTION", "scene_number": 2, "description": "How did the king of phones destroy itself?", "mini_arc_phase": "BUILD"},
                    {"phase": "CONTEXT", "scene_number": 3, "description": "The golden age of Finnish engineering dominance", "mini_arc_phase": "COMPLICATION"},
                    {"phase": "FIRST_DISCOVERY", "scene_number": 4, "description": "The 2004 touchscreen prototype hidden in the vault", "mini_arc_phase": "REVEAL"},
                    {"phase": "COMPLICATION", "scene_number": 5, "description": "Symbian's crumbling spaghetti code nightmare", "mini_arc_phase": "CONSEQUENCE"},
                    {"phase": "ESCALATION", "scene_number": 6, "description": "The iPhone arrives while executives remain in denial", "mini_arc_phase": "SETUP"},
                    {"phase": "REVELATION", "scene_number": 7, "description": "Culture of fear: middle managers falsifying progress reports", "mini_arc_phase": "REVEAL"},
                    {"phase": "CONSEQUENCE", "scene_number": 8, "description": "The Burning Platform memo and stock collapse", "mini_arc_phase": "CONSEQUENCE"},
                    {"phase": "DEEPER_REVELATION", "scene_number": 9, "description": "Hardware supremacy became their software prison", "mini_arc_phase": "REVEAL"},
                    {"phase": "FINAL_CONTRADICTION", "scene_number": 10, "description": "The giant sold for parts to Microsoft", "mini_arc_phase": "COMPLICATION"},
                    {"phase": "PAYOFF", "scene_number": 11, "description": "The final lingering lesson of software disruption", "mini_arc_phase": "PAYOFF"}
                ],
                "acts": [
                    {"act_number": 1, "title": "Act I: The Golden Fortress & The Hidden Crack", "scenes": [1, 2, 3, 4]},
                    {"act_number": 2, "title": "Act II: The Code Collapse & The Culture of Fear", "scenes": [5, 6, 7, 8]},
                    {"act_number": 3, "title": "Act III: The Burning Platform & The Legacy", "scenes": [9, 10, 11]}
                ]
            }
        elif cls_name == "ScriptwriterAgent":
            return [
                {
                    "scene_number": 1,
                    "narrative_intent": "HOOK",
                    "mini_arc_phase": "SETUP",
                    "voiceover": "2007 में दुनिया का हर दूसरा स्मार्टफोन नोकिया का था। लेकिन सिर्फ पांच सालों के अंदर, ढाई सौ अरब डॉलर का यह साम्राज्य पूरी तरह खाक हो गया।",
                    "caption": "In 2007, every second smartphone on Earth was Nokia. But within five years, this $250 billion empire vanished into thin air."
                },
                {
                    "scene_number": 2,
                    "narrative_intent": "CENTRAL_QUESTION",
                    "mini_arc_phase": "BUILD",
                    "voiceover": "सवाल यह नहीं है कि नोकिया हारा कैसे—सवाल यह है कि जिस कंपनी ने भविष्य का पहला टचस्क्रीन फोन खुद बनाया था, उसने उसे अपनी तिजोरी में क्यों दफन कर दिया?",
                    "caption": "The question isn't just how Nokia lost—it is why the company that invented the first touchscreen phone buried it in its own vault."
                },
                {
                    "scene_number": 3,
                    "narrative_intent": "FIRST_DISCOVERY",
                    "mini_arc_phase": "REVEAL",
                    "voiceover": "आईफोन से तीन साल पहले, नोकिया के इंजीनियरों ने एक सीक्रेट टचस्क्रीन प्रोटोटाइप तैयार किया था। लेकिन बोर्डरूम ने इसे फिजूल मानकर खारिज कर दिया।",
                    "caption": "Three years before the iPhone, Nokia engineers built a secret touchscreen prototype. But the boardroom dismissed it as an unnecessary gimmick."
                },
                {
                    "scene_number": 4,
                    "narrative_intent": "REVELATION",
                    "mini_arc_phase": "CONSEQUENCE",
                    "voiceover": "सच्चाई यह थी कि नोकिया का ऑपरेटिंग सिस्टम अंदर से सड़ चुका था। एक छोटा सा फीचर जोड़ने के लिए सत्तावन अलग-अलग कोड फाइल्स बदलनी पड़ती थीं।",
                    "caption": "The truth was Nokia's operating system was rotting from inside. Adding a single feature required modifying fifty-seven separate code files."
                },
                {
                    "scene_number": 5,
                    "narrative_intent": "PAYOFF",
                    "mini_arc_phase": "PAYOFF",
                    "voiceover": "नोकिया हार्डवेयर में बेमिसाल था, लेकिन सॉफ्टवेयर की नई दुनिया में उसकी बादशाहत सिर्फ एक याद बनकर रह गई।",
                    "caption": "Nokia was unmatched in hardware, but in the new era of software, its reign became nothing more than a memory."
                }
            ]
        elif cls_name == "DirectorAgent":
            return {
                "schema_version": "2.0",
                "project_meta": {
                    "topic": "The Fall of Nokia",
                    "genre": "documentary",
                    "style_profile": "DOCUMENTARY_INVESTIGATIVE",
                    "language": "hindi",
                    "visual_bible": {
                        "era": "2000s",
                        "locations": ["Espoo, Finland", "USA"],
                        "lighting": "cinematic low-key dramatic",
                        "color_language": "cool noir tones",
                        "film_texture": "subtle grain 35mm"
                    }
                },
                "documentary_vision": {
                    "topic": "The Fall of Nokia",
                    "core_premise": "The internal organizational decay of a technology titan",
                    "central_question": "How did Nokia collapse despite having immense R&D resources?",
                    "documentary_thesis": "Architectural software paralysis and corporate denial destroyed Nokia.",
                    "central_contradiction": "Invented touchscreen concepts first, but delivered inferior software.",
                    "hook_strategy": {
                        "hook_type": "CONTRADICTION",
                        "target_duration_seconds": 25.0,
                        "anomaly_description": "Dominant 50% market share turning into complete collapse in 5 years",
                        "withholding_element": "Withhold early origins to focus on the dramatic crash",
                        "opening_visual_cue": "Macro shot of cracked Nokia screen"
                    },
                    "macro_narrative_arc": [
                        {"phase": "HOOK", "target_beat_index": 0, "narrative_goal": "Establish anomaly", "attention_target": 0.85},
                        {"phase": "CENTRAL_QUESTION", "target_beat_index": 1, "narrative_goal": "Pose investigative core inquiry", "attention_target": 0.75}
                    ],
                    "mini_arcs": [
                        {"beat_id": "b001", "time_window": "0:00 - 0:30", "setup": "Nokia peak", "build": "iPhone emergence", "complication": "Codebase paralysis", "reveal": "Shelved prototype", "consequence": "Market share erosion"}
                    ],
                    "visual_motifs": ["Nokia blue logo banner", "Cracked screen glass", "Ticking stopwatch"],
                    "ending_image": "A pristine Nokia 3310 lying silently on an abandoned testing bench.",
                    "pacing_and_restraint": "Enforce static holds on evidence and deliberate silence on major reveals",
                    "style_profile": "DOCUMENTARY_INVESTIGATIVE"
                },
                "research_package": research_pkg,
                "story_beats": [
                    {
                        "beat_id": "b001",
                        "time_context": {
                            "year": "2000s",
                            "mode": "historical",
                            "location": "Espoo, Finland",
                            "transition_reason": "Establishing historical market dominance"
                        },
                        "narrative_intent": "HOOK",
                        "mini_arc_phase": "SETUP",
                        "visual_sequence_plan": {
                            "intention": "Cinematically demonstrate the sudden collapse of undisputed dominance",
                            "visual_argument": "uncontested_hardware_glory vs hidden_software_decay",
                            "withholding_strategy": "Withhold full financial charts until showing physical assembly line scale",
                            "memorable_image": "A cracked glowing Nokia screen amidst abandoned Finnish design blueprints",
                            "sequence_ending_statement": "Static hold on a lonely phone on a dark executive desk",
                            "information_change": 0.8,
                            "emotional_change": 0.75,
                            "visual_change": 0.85,
                            "scale_change": 0.65
                        },
                        "description": "The Mobile Giant & The $250B Evaporation",
                        "attention_intensity": 0.85,
                        "chapter_color_language": "cool noir tones",
                        "narration_blocks": [
                            {
                                "block_id": "n001",
                                "voiceover": "2007 में दुनिया का हर दूसरा स्मार्टफोन नोकिया का था। लेकिन सिर्फ पांच सालों के अंदर, ढाई सौ अरब डॉलर का यह साम्राज्य पूरी तरह खाक हो गया।",
                                "caption": "In 2007, every second smartphone on Earth was Nokia. But within five years, this $250 billion empire vanished into thin air.",
                                "duration_hint": 4.5,
                                "strategic_silence": {
                                    "duration_seconds": 0.5,
                                    "position": "end",
                                    "ambient_level": -35,
                                    "visual_behavior": "hold_frame"
                                },
                                "audio_metadata": {
                                    "music_energy": 0.6,
                                    "music_duck_amount": -15
                                },
                                "mini_arc_phase": "SETUP",
                                "shots": [
                                    {
                                        "shot_id": "n001_s001",
                                        "duration_mode": "ratio",
                                        "duration_ratio": 0.5,
                                        "shot_role": "ESTABLISHING",
                                        "asset_provenance": "STOCK",
                                        "shot_size": "wide",
                                        "camera_angle": "eye_level",
                                        "lens": "wide_angle_lens",
                                        "composition": "rule_of_thirds",
                                        "visual_job": "ESTABLISH_WORLD",
                                        "shot_relationship": "CONTINUATION",
                                        "visual_type": "ai_image",
                                        "fallback_type": "MapFallback",
                                        "visual_description": "Wide panoramic view of Nokia corporate headquarters in Espoo, Finland under cold morning light.",
                                        "visual_query": "Nokia headquarters Espoo Finland corporate exterior 2000s",
                                        "ai_prompt": "Nokia corporate headquarters, 2000s, Espoo Finland, glass modern architecture, cold morning light, cinematic wide shot",
                                        "camera_motion": "slow_push_in",
                                        "motion_intensity": 0.25,
                                        "transition_in": "hard_cut",
                                        "cut_reason": "establish_epicenter_of_mobile_empire",
                                        "visual_importance": 0.8,
                                        "visual_density": 0.4,
                                        "is_restrained": False,
                                        "continuity": {
                                            "group_id": "grp1",
                                            "characters": [],
                                            "location": "Espoo, Finland",
                                            "environment": "exterior corporate headquarters",
                                            "time_period": "2000s",
                                            "lighting": "cold morning daylight"
                                        }
                                    },
                                    {
                                        "shot_id": "n001_s002",
                                        "duration_mode": "ratio",
                                        "duration_ratio": 0.5,
                                        "shot_role": "DETAIL",
                                        "asset_provenance": "DOCUMENT",
                                        "shot_size": "close",
                                        "camera_angle": "overhead_shot",
                                        "lens": "macro_lens",
                                        "composition": "center_framed",
                                        "visual_job": "SHOW_SCALE",
                                        "shot_relationship": "NUMBER_TO_SCALE",
                                        "visual_type": "motion_graphics",
                                        "fallback_type": "CinematicText",
                                        "visual_description": "Kinetic typography overlay revealing $250,000,000,000 market value lost.",
                                        "visual_query": "market value financial crash chart 2000s",
                                        "ai_prompt": "Financial crash typography, $250 billion loss, red warning indicators, macro dark background",
                                        "camera_motion": "static",
                                        "motion_intensity": 0.0,
                                        "transition_in": "hard_cut",
                                        "cut_reason": "punctuate_scale_of_financial_collapse",
                                        "visual_importance": 0.9,
                                        "visual_density": 0.7,
                                        "is_restrained": True,
                                        "continuity": {
                                            "group_id": "grp1",
                                            "characters": [],
                                            "location": "Espoo, Finland",
                                            "environment": "data stream interface",
                                            "time_period": "2000s",
                                            "lighting": "dark room monitor glow"
                                        },
                                        "editorial_events": [
                                            {
                                                "type": "NUMBER_REVEAL",
                                                "cue": "$250,000,000,000",
                                                "timing_percent": 10.0,
                                                "intensity": 0.9,
                                                "reason": "Dramatic punctuation of financial collapse"
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "block_id": "n002",
                                "voiceover": "आईफोन से तीन साल पहले, नोकिया के इंजीनियरों ने एक सीक्रेट टचस्क्रीन प्रोटोटाइप तैयार किया था। लेकिन बोर्डरूम ने इसे खारिज कर दिया।",
                                "caption": "Three years before the iPhone, Nokia engineers built a secret touchscreen prototype. But the boardroom dismissed it.",
                                "duration_hint": 4.5,
                                "strategic_silence": {
                                    "duration_seconds": 0.5,
                                    "position": "end",
                                    "ambient_level": -35,
                                    "visual_behavior": "hold_frame"
                                },
                                "audio_metadata": {
                                    "music_energy": 0.5,
                                    "music_duck_amount": -15
                                },
                                "mini_arc_phase": "REVEAL",
                                "shots": [
                                    {
                                        "shot_id": "n002_s001",
                                        "duration_mode": "ratio",
                                        "duration_ratio": 1.0,
                                        "shot_role": "EVIDENCE",
                                        "asset_provenance": "DOCUMENT",
                                        "shot_size": "close",
                                        "camera_angle": "low_angle",
                                        "lens": "macro_lens",
                                        "composition": "rule_of_thirds",
                                        "visual_job": "EXAMINE_EVIDENCE",
                                        "shot_relationship": "EVIDENCE_TO_REVEAL",
                                        "visual_type": "ai_image",
                                        "fallback_type": "ClassifiedFile",
                                        "visual_description": "Secret 2004 touchscreen prototype design blueprint with engineering annotations.",
                                        "visual_query": "secret touchscreen phone prototype blueprint 2004",
                                        "ai_prompt": "Confidential engineering blueprint, 2004 capacitive touchscreen phone, technical annotations, warm tungsten desk lamp",
                                        "camera_motion": "slow_push_in",
                                        "motion_intensity": 0.2,
                                        "transition_in": "hard_cut",
                                        "cut_reason": "reveal_shelved_touchscreen_prototype_evidence",
                                        "visual_importance": 0.85,
                                        "visual_density": 0.6,
                                        "is_restrained": True,
                                        "continuity": {
                                            "group_id": "grp1",
                                            "characters": [],
                                            "location": "Espoo, Finland",
                                            "environment": "R&D research laboratory",
                                            "time_period": "2004",
                                            "lighting": "tungsten desk lamp"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        elif cls_name == "QCEditorAgent":
            return {"status": "APPROVED", "score": 9, "feedback": "Excellent script structure and director metadata."}
        return {"status": "ok"}
            
    def _extract_json(self, text):
        """Robustly extract JSON (array or object) from markdown/reasoning blocks."""
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"```json|```", "", text).strip()
        
        # Handle trailing commas
        text = re.sub(r",(\s*[}\]])", r"\1", text)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except: pass
                        
        raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")

    def _call_groq(self, prompt, system_prompt, require_json):
        groq_key = os.environ.get("GROQ_KEY", "")
        if not groq_key:
            raise Exception("GROQ_KEY not found for fallback")
        from groq import Groq
        client = Groq(api_key=groq_key)
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            temperature=0.8, max_tokens=4000
        )
        output = r.choices[0].message.content.strip()
        if require_json:
            return self._extract_json(output)
        return output

    def call_llm(self, prompt, system_prompt="", retries=4, require_json=True):
        """Calls the LLM and returns the parsed JSON response."""
        
        if BaseAgent.FORCE_GROQ:
            log.info(f"[{self.__class__.__name__}] Bypassing Gemini (Force Groq is active)")
            try:
                return self._call_groq(prompt, system_prompt, require_json)
            except Exception as e:
                log.error(f"[{self.__class__.__name__}] Groq call failed: {e}")
                if not os.environ.get("GEMINI_KEY") and not os.environ.get("GROQ_KEY"):
                    return self._get_mock_fallback(prompt, system_prompt, require_json)
                raise e

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"
            
        gemini_key_1 = os.environ.get("GEMINI_KEY", "")
        gemini_key_2 = os.environ.get("GEMINI_KEY_2", "")
        current_key = gemini_key_1
            
        if not gemini_key_1 and not os.environ.get("GROQ_KEY"):
            return self._get_mock_fallback(prompt, system_prompt, require_json)

        for attempt in range(retries):
            try:
                log.info(f"[{self.__class__.__name__}] Calling LLM (Attempt {attempt+1}/{retries})")
                
                if not self.model:
                    raise Exception("Gemini model not initialized (no key)")
                response = self.model.generate_content(full_prompt)
                
                if not response or not response.text:
                    raise Exception("Empty response from LLM")
                    
                output = response.text
                
                if require_json:
                    return self._extract_json(output)
                return output
                
            except Exception as e:
                err_str = str(e)
                log.error(f"[{self.__class__.__name__}] LLM Call failed: {err_str}")
                if attempt < retries - 1:
                    sleep_time = 5
                    match = re.search(r"retry in ([\d\.]+)s", err_str)
                    if match:
                        sleep_time = float(match.group(1)) + 1.5
                        log.info(f"Rate limited. Detected required sleep: {sleep_time:.1f}s")
                    
                    log.info(f"[{self.__class__.__name__}] Waiting {sleep_time:.1f}s for rate limit reset...")
                    time.sleep(sleep_time)
                else:
                    # Worst-case scenario: Gemini exhausted all retries. Try Groq.
                    log.warning(f"[{self.__class__.__name__}] Gemini exhausted all retries! Falling back to Groq Llama-3.3-70B (Worst-case)...")
                    try:
                        res = self._call_groq(prompt, system_prompt, require_json)
                        BaseAgent.FORCE_GROQ = True # Flip switch for subsequent agents
                        return res
                    except Exception as groq_e:
                        log.error(f"[{self.__class__.__name__}] Groq fallback also failed: {groq_e}")
                        if not os.environ.get("GEMINI_KEY") and not os.environ.get("GROQ_KEY"):
                            return self._get_mock_fallback(prompt, system_prompt, require_json)
                        raise e
                    
        return None
