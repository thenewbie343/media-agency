with open("agents/scriptwriter.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """2. WORD WEIGHT:
       To give words gravity, use short sentences. 
       DO NOT put dashes or ellipses between every word! It breaks the TTS engine.
       YES: "But that night. One man. Refused to press the button."
       NOT: "But that night — one man — refused to press the button."
       NOT: "The loss... two hundred... billion dollars... gone."
    
    3. DRAMATIC PACING:
       Use short, punchy sentences for suspenseful pauses before revelations:
       "And when they opened the file. Everything changed."
       "The radar showed five incoming missiles. Heading straight for Moscow." """

replacement1 = """2. WORD WEIGHT:
       To give words gravity, DO NOT put dashes or ellipses between every word! DO NOT write single word sentences! It breaks the TTS engine.
       YES: "But that night, one man refused to press the button."
       NOT: "But that night. One man. Refused to press the button."
       NOT: "The loss... two hundred... billion dollars... gone."
    
    3. DRAMATIC PACING:
       Use natural punctuation. Avoid artificial pauses that sound like stammering.
       "And when they opened the file, everything changed."
       "The radar showed five incoming missiles heading straight for Moscow." """

target2 = """2. WORD WEIGHT:
     To give words gravity, use short sentences. 
     DO NOT put dashes or ellipses between every word! It breaks the TTS engine.
     YES: "But that night. One man. Refused to press the button."
     NOT: "But that night — one man — refused to press the button."
  
  3. DRAMATIC PACING:
     Use short, punchy sentences for suspenseful pauses before revelations:
     "And when they opened the file. Everything changed." """

replacement2 = """2. WORD WEIGHT:
     To give words gravity, DO NOT put dashes or ellipses between every word! DO NOT write single word sentences! It breaks the TTS engine.
     YES: "But that night, one man refused to press the button."
     NOT: "But that night. One man. Refused to press the button."
     NOT: "But that night — one man — refused to press the button."
  
  3. DRAMATIC PACING:
     Use natural punctuation. Avoid artificial pauses that sound like stammering.
     "And when they opened the file, everything changed." """

content = content.replace(target1.strip(), replacement1.strip())
content = content.replace(target2.strip(), replacement2.strip())

with open("agents/scriptwriter.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done safe replace!")
