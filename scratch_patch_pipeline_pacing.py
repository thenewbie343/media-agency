import re
with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"text = re\.sub\(r'\[—–-\]', ',', text\)\s*text = re\.sub\(r'\\\.{2,}', ',', text\)\s*text = re\.sub\(r',{2,}', ',', text\)"
replacement = """# Strip dashes and ellipses to spaces for smoother TTS pacing (prevent stammering)
        text = re.sub(r'[—–-]', ' ', text)
        text = re.sub(r'\.{2,}', ' ', text)
        text = re.sub(r',{2,}', ',', text)
        text = re.sub(r'\s+', ' ', text).strip()"""

new_content, count = re.subn(pattern, replacement, content)
if count > 0:
    with open("pipeline.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patched pipeline.py pacing logic!")
else:
    print("Target not found.")
