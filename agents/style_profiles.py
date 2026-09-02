"""
Reference-Aware Cinematic Style Profiles & Look Bibles
Defines genre-specific directorial rules for pacing, cinematography, graphics, color, and restraint.
"""

from typing import Dict, Any, List

STYLE_PROFILES: Dict[str, Dict[str, Any]] = {
    "DOCUMENTARY_INVESTIGATIVE": {
        "name": "Investigative Crime & Financial Documentary",
        "description": "Vox / Netflix investigative style with cold noir tones, heavy archival evidence, and staccato tension.",
        "pacing": {
            "min_shot_duration": 1.2,
            "max_shot_duration": 4.2,
            "target_avg_duration": 3.0,
            "montage_allowed": True
        },
        "cinematography": {
            "preferred_shot_sizes": ["extreme_close", "close", "medium", "wide"],
            "preferred_angles": ["low_angle", "eye_level", "dutch_angle"],
            "preferred_motions": ["slow_push_in", "pan_left", "static", "dolly_in"],
            "static_probability": 0.35,
            "macro_detail_frequency": 0.4
        },
        "visual_strategy": {
            "archival_preference": 0.45,
            "motion_graphics_preference": 0.30,
            "ai_reconstruction_preference": 0.25,
            "preferred_fallbacks": ["ClassifiedFile", "EvidenceBoard", "ArchivalDocument"]
        },
        "color_and_lighting": {
            "chapter_luts": ["noir", "high_contrast", "vintage_film"],
            "lighting_style": "low-key, cold, contrasty, fluorescent shadows",
            "overlay_style": "dust_scratches",
            "overlay_frequency": 0.25
        },
        "audio_and_sound": {
            "sound_density": "restrained",
            "silence_frequency": 0.25,
            "music_mood": "dark suspense",
            "foley_cues": ["paper_rustle", "deep_impact"]
        },
        "restraint": {
            "restraint_frequency": 0.30,
            "static_hold_on_reveal": True
        }
    },
    "DOCUMENTARY_PREMIUM": {
        "name": "Masterclass / BBC High-End Documentary",
        "description": "Measured, elegant cinematic aesthetic with golden hour lighting, wide vistas, and breathing room.",
        "pacing": {
            "min_shot_duration": 2.5,
            "max_shot_duration": 5.0,
            "target_avg_duration": 3.8,
            "montage_allowed": False
        },
        "cinematography": {
            "preferred_shot_sizes": ["wide", "medium", "medium_close", "extreme_wide"],
            "preferred_angles": ["eye_level", "low_angle"],
            "preferred_motions": ["slow_push_in", "pan_right", "crane_up", "static"],
            "static_probability": 0.40,
            "macro_detail_frequency": 0.2
        },
        "visual_strategy": {
            "archival_preference": 0.35,
            "motion_graphics_preference": 0.20,
            "ai_reconstruction_preference": 0.45,
            "preferred_fallbacks": ["PortraitCard", "CinematicText"]
        },
        "color_and_lighting": {
            "chapter_luts": ["warm_cinema", "teal_orange"],
            "lighting_style": "golden hour, cinematic diffusion, anamorphic flare",
            "overlay_style": "film_grain",
            "overlay_frequency": 0.15
        },
        "audio_and_sound": {
            "sound_density": "minimal",
            "silence_frequency": 0.30,
            "music_mood": "cinematic dramatic",
            "foley_cues": ["subtle_whoosh"]
        },
        "restraint": {
            "restraint_frequency": 0.40,
            "static_hold_on_reveal": True
        }
    },
    "DOCUMENTARY_TECH": {
        "name": "Cyber Warfare & Tech Deep-Dive",
        "description": "Modern technical investigation with network topologies, terminal screens, and neon glitch touches.",
        "pacing": {
            "min_shot_duration": 1.0,
            "max_shot_duration": 3.8,
            "target_avg_duration": 2.6,
            "montage_allowed": True
        },
        "cinematography": {
            "preferred_shot_sizes": ["close", "extreme_close", "medium"],
            "preferred_angles": ["eye_level", "overhead_shot"],
            "preferred_motions": ["pan_left", "pan_right", "slow_push_in", "static"],
            "static_probability": 0.25,
            "macro_detail_frequency": 0.5
        },
        "visual_strategy": {
            "archival_preference": 0.20,
            "motion_graphics_preference": 0.50,
            "ai_reconstruction_preference": 0.30,
            "preferred_fallbacks": ["TechnicalDiagram", "AnimatedDiagram", "Timeline"]
        },
        "color_and_lighting": {
            "chapter_luts": ["high_contrast", "noir", "neon_cyberpunk"],
            "lighting_style": "cool LED, blue-green server glow, deep blacks",
            "overlay_style": "vhs_glitch",
            "overlay_frequency": 0.30
        },
        "audio_and_sound": {
            "sound_density": "moderate",
            "silence_frequency": 0.15,
            "music_mood": "serious corporate",
            "foley_cues": ["deep_impact", "subtle_whoosh"]
        },
        "restraint": {
            "restraint_frequency": 0.20,
            "static_hold_on_reveal": False
        }
    },
    "DOCUMENTARY_HISTORY": {
        "name": "Historical Archival Retrospective",
        "description": "Period-accurate archival case file with 35mm grain, sepia tones, and authentic historical records.",
        "pacing": {
            "min_shot_duration": 2.0,
            "max_shot_duration": 4.5,
            "target_avg_duration": 3.4,
            "montage_allowed": False
        },
        "cinematography": {
            "preferred_shot_sizes": ["medium", "close", "wide"],
            "preferred_angles": ["eye_level", "low_angle"],
            "preferred_motions": ["slow_push_in", "dolly_out", "static"],
            "static_probability": 0.45,
            "macro_detail_frequency": 0.3
        },
        "visual_strategy": {
            "archival_preference": 0.60,
            "motion_graphics_preference": 0.15,
            "ai_reconstruction_preference": 0.25,
            "preferred_fallbacks": ["ArchivalDocument", "Newspaper", "PhotoWall"]
        },
        "color_and_lighting": {
            "chapter_luts": ["vintage_film", "sepia", "warm_cinema"],
            "lighting_style": "warm archival, incandescent table lamps, period atmosphere",
            "overlay_style": "film_grain",
            "overlay_frequency": 0.35
        },
        "audio_and_sound": {
            "sound_density": "minimal",
            "silence_frequency": 0.35,
            "music_mood": "investigative mystery",
            "foley_cues": ["paper_rustle"]
        },
        "restraint": {
            "restraint_frequency": 0.35,
            "static_hold_on_reveal": True
        }
    },
    "DOCUMENTARY_FAST_PACED": {
        "name": "Fast-Paced Explainer / Viral Hook",
        "description": "High-retention rhythmic explainer with frequent density contrast and impact punctuation.",
        "pacing": {
            "min_shot_duration": 0.8,
            "max_shot_duration": 3.0,
            "target_avg_duration": 2.0,
            "montage_allowed": True
        },
        "cinematography": {
            "preferred_shot_sizes": ["extreme_close", "close", "wide", "extreme_wide"],
            "preferred_angles": ["dutch_angle", "low_angle", "overhead_shot"],
            "preferred_motions": ["slow_push_in", "pan_left", "pan_right", "dolly_in"],
            "static_probability": 0.15,
            "macro_detail_frequency": 0.4
        },
        "visual_strategy": {
            "archival_preference": 0.30,
            "motion_graphics_preference": 0.45,
            "ai_reconstruction_preference": 0.25,
            "preferred_fallbacks": ["CinematicText", "Timeline", "EvidenceBoard"]
        },
        "color_and_lighting": {
            "chapter_luts": ["high_contrast", "teal_orange"],
            "lighting_style": "high key, vivid, punchy commercial lighting",
            "overlay_style": "light_leaks",
            "overlay_frequency": 0.20
        },
        "audio_and_sound": {
            "sound_density": "rhythmic",
            "silence_frequency": 0.10,
            "music_mood": "calm focus",
            "foley_cues": ["deep_impact", "subtle_whoosh"]
        },
        "restraint": {
            "restraint_frequency": 0.15,
            "static_hold_on_reveal": False
        }
    }
}

def get_style_profile(profile_name: str = "DOCUMENTARY_INVESTIGATIVE") -> Dict[str, Any]:
    clean_name = str(profile_name).upper().strip()
    return STYLE_PROFILES.get(clean_name, STYLE_PROFILES["DOCUMENTARY_INVESTIGATIVE"])

def select_profile_for_topic(topic: str, genre: str = "documentary") -> str:
    t_lower = (str(topic) + " " + str(genre)).lower()
    if any(w in t_lower for w in ["hack", "cyber", "code", "tech", "bitcoin", "digital", "internet", "ai", "gps"]):
        return "DOCUMENTARY_TECH"
    if any(w in t_lower for w in ["scam", "bank", "heist", "murder", "crime", "investigation", "fraud", "mallya", "scandal"]):
        return "DOCUMENTARY_INVESTIGATIVE"
    if any(w in t_lower for w in ["history", "war", "ancient", "century", "empire", "19", "18", "vintage"]):
        return "DOCUMENTARY_HISTORY"
    if any(w in t_lower for w in ["fast", "short", "viral", "reel", "explainer", "quick"]):
        return "DOCUMENTARY_FAST_PACED"
    return "DOCUMENTARY_INVESTIGATIVE"
