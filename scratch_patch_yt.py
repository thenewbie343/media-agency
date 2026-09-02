import re
with open("agents/youtube_discovery.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"def youtube_search_by_claim\(claim_text: str, max_results: int = 5,\s*channel_filter: Optional\[str\] = None\) -> list:"

replacement = """_YOUTUBE_UNAUTHORIZED = False

def youtube_search_by_claim(claim_text: str, max_results: int = 5,
                            channel_filter: Optional[str] = None) -> list:
    global _YOUTUBE_UNAUTHORIZED
    if _YOUTUBE_UNAUTHORIZED:
        return []"""

new_content, count = re.subn(pattern, replacement, content)

# Now find where the 403 error happens
pattern_2 = r"        resp = requests\.get\(search_url, \*\*kwargs\)\s*if resp\.status_code != 200:\s*log\.warning\(f\"YouTube Search API returned \{resp\.status_code\}: \{resp\.text\[:200\]\}\"\)\s*return \[\]"

replacement_2 = """        resp = requests.get(search_url, **kwargs)
        if resp.status_code != 200:
            log.warning(f"YouTube Search API returned {resp.status_code}: {resp.text[:200]}")
            if resp.status_code == 403:
                global _YOUTUBE_UNAUTHORIZED
                _YOUTUBE_UNAUTHORIZED = True
                log.warning("YouTube API returned 403. Marking YouTube source as UNAUTHORIZED/OFFLINE for the rest of the run to prevent spam.")
            return []"""

new_content, count2 = re.subn(pattern_2, replacement_2, new_content)

if count > 0 and count2 > 0:
    with open("agents/youtube_discovery.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patched youtube_discovery.py!")
else:
    print(f"Target not found. {count}, {count2}")
