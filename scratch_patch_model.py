import glob

for f in ["agents/asset_verifier.py", "agents/rendered_experience_critic.py"]:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    content = content.replace("gemini-2.0-flash", "gemini-3.6-flash")
    
    with open(f, "w", encoding="utf-8") as file:
        file.write(content)

print("Replaced gemini-2.0-flash with gemini-3.6-flash!")
