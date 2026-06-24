import requests, os, json

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GH_TOKEN = os.environ["GH_TOKEN"]
GH_REPO = os.environ["GH_REPO"]

# Get last processed update ID (stored as a repo variable)
def get_last_update_id():
    url = f"https://api.github.com/repos/{GH_REPO}/actions/variables/LAST_UPDATE_ID"
    r = requests.get(url, headers={"Authorization": f"token {GH_TOKEN}"})
    if r.status_code == 200:
        return int(r.json().get("value", "0"))
    return 0

def set_last_update_id(uid):
    url = f"https://api.github.com/repos/{GH_REPO}/actions/variables/LAST_UPDATE_ID"
    requests.patch(url,
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github+json"},
        json={"value": str(uid)}
    )

def trigger_pipeline(topic, time):
    url = f"https://api.github.com/repos/{GH_REPO}/dispatches"
    requests.post(url,
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github+json"},
        json={"event_type": "make_video",
              "client_payload": {"raw_input": text.replace("/make ","").strip(), "time": time_val}
    )

last_id = get_last_update_id()
updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id + 1}&limit=10"
resp = requests.get(updates_url).json()

for update in resp.get("result", []):
    uid = update["update_id"]
    msg = update.get("message", {})
    text = msg.get("text", "")
    chat = str(msg.get("chat", {}).get("id", ""))

    if chat == CHAT_ID and text.startswith("/make"):
        parts = text.replace("/make ", "").strip().split(" ")
        time_val = parts[-1] if ":" in parts[-1] else "18:00"
        topic = " ".join(parts[:-1]) if ":" in parts[-1] else " ".join(parts)
        trigger_pipeline(topic, time_val)
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID,
                  "text": f"✅ Got it! Starting pipeline for: {topic}"})

    set_last_update_id(uid)
