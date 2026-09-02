with open("agents/director.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """                    # 2. ELIMINATE CAMERA FATIGUE (STRICTLY BAN ZOOM_IN REPETITION)
                    motion = shot.get("camera_motion", "static")
                    if motion == "zoom_in" or motion == last_motion or not motion:
                        available_motions = [m for m in motions if m != last_motion and m != "zoom_in"]
                        shot["camera_motion"] = available_motions[m_idx % len(available_motions)]
                        m_idx += 1
                    last_motion = shot["camera_motion"]"""

replacement = """                    # 2. ELIMINATE CAMERA FATIGUE (STRICTLY BAN ZOOM_IN REPETITION AND A-B-A-B)
                    motion = shot.get("camera_motion", "static")
                    if motion == "zoom_in" or motion in last_two_motions or not motion:
                        available_motions = [m for m in motions if m not in last_two_motions and m != "zoom_in"]
                        shot["camera_motion"] = available_motions[m_idx % len(available_motions)]
                        m_idx += 1
                    
                    last_two_motions.append(shot["camera_motion"])
                    if len(last_two_motions) > 2:
                        last_two_motions.pop(0)"""

content = content.replace("last_motion = None", "last_two_motions = []")
content = content.replace(target, replacement)

with open("agents/director.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done fixing A-B-A-B!")
