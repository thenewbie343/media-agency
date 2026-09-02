import re
with open("agents/scriptwriter.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"  2\. WORD WEIGHT:.*?Everything changed\.\""
replacement = """  2. WORD WEIGHT:
       To give words gravity, DO NOT put dashes or ellipses between every word! DO NOT write single word sentences! It breaks the TTS engine.
       YES: "But that night, one man refused to press the button."
       NOT: "But that night. One man. Refused to press the button."
       NOT: "But that night — one man — refused to press the button."
    
  3. DRAMATIC PACING:
       Use natural punctuation. Avoid artificial pauses that sound like stammering.
       "And when they opened the file, everything changed.\""""

new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
if count > 0:
    with open("agents/scriptwriter.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Patched {count} places!")
else:
    print("Target not found.")
