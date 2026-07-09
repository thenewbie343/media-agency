"""
telegram_listener.py v3.0 — Fixed and final
Triggered by cron-job.org every minute via workflow_dispatch.
Supports /make and /help commands.
"""
import requests, os, json, re

TOKEN    = os.environ["TELEGRAM_TOKEN"]
CHAT_ID  = str(os.environ["TELEGRAM_CHAT_ID"])
GH_TOKEN = os.environ["GH_TOKEN"]
GH_REPO  = os.environ["GH_REPO"]

def get_last_uid():
    url = f"https://api.github.com/repos/{GH_REPO}/actions/variables/LAST_UPDATE_ID"
    r = requests.get(url, headers={
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json"
    }, timeout=10)
    if r.status_code == 200:
        return int(r.json().get("value", "0"))
    return 0

def set_last_uid(uid):
    url = f"https://api.github.com/repos/{GH_REPO}/actions/variables/LAST_UPDATE_ID"
    requests.patch(url, headers={
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json"
    }, json={"value": str(uid)}, timeout=10)

def trigger_pipeline(topic, niche="", script=""):
    url = f"https://api.github.com/repos/{GH_REPO}/dispatches"
    requests.post(url, headers={
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github+json"
    }, json={
        "event_type": "make_video",
        "client_payload": {
            "topic": topic,
            "niche": niche,
            "script": script
        }
    }, timeout=10)

def send_tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )

# Get last processed update
last_uid = get_last_uid()
resp = requests.get(
    f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_uid + 1}&limit=10",
    timeout=15
).json()

for update in resp.get("result", []):
    uid  = update["update_id"]
    msg  = update.get("message", {})
    text = msg.get("text", "").strip()
    chat = str(msg.get("chat", {}).get("id", ""))

    if chat != CHAT_ID:
        set_last_uid(uid)
        continue

    # /make command — manual video
    if text.lower().startswith("/make"):
        raw = text[5:].strip()
        if not raw:
            send_tg("❌ Format: /make [topic] [HH:MM]\nExample: /make Paytm का सच 18:00")
        else:
            trigger_pipeline(topic=raw, niche="", script="")
            send_tg(
                f"✅ Starting pipeline!\n"
                f"📌 {raw}\n\n"
                f"I'll update you at each stage (~10-15 min)"
            )

    # /daily command — trigger today's daily videos manually
    elif text.lower() == "/daily":
        url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/daily_scheduler.yml/dispatches"
        requests.post(url, headers={
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github+json"
        }, json={"ref": "main"}, timeout=10)
        send_tg("📅 Daily scheduler triggered! Making today's 3 videos.")

    # /status command
    elif text.lower() == "/status":
        url = f"https://api.github.com/repos/{GH_REPO}/actions/runs?per_page=3"
        r = requests.get(url, headers={
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github+json"
        }, timeout=10)
        runs = r.json().get("workflow_runs", [])
        if runs:
            lines = ["📊 Recent pipeline runs:\n"]
            for run in runs[:3]:
                status = run.get("conclusion") or run.get("status","running")
                name   = run.get("name","")[:30]
                emoji  = "✅" if status=="success" else "❌" if status=="failure" else "🔄"
                lines.append(f"{emoji} {name} — {status}")
            send_tg("\n".join(lines))
        else:
            send_tg("No recent runs found.")

    # /help command
    elif text.lower() == "/help":
        send_tg(
            "🎬 Hindi YouTube Agency Bot\n\n"
            "Commands:\n\n"
            "▶️ /make [topic] [HH:MM]\n"
            "Manual video with auto genre detection\n"
            "Example: /make Paytm का सच 18:00\n\n"
            "▶️ /make [topic] --genre documentary --lang hindi --duration 8 [HH:MM]\n"
            "Full manual control\n\n"
            "▶️ /daily\n"
            "Trigger today's scheduled videos now\n\n"
            "▶️ /status\n"
            "Check recent pipeline runs\n\n"
            "📌 Daily videos run automatically at 11:30 AM IST\n"
            "📁 Update topics.json in GitHub repo to change schedule"
        )

    set_last_uid(uid)

print("Listener done")
