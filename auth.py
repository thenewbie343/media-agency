"""
auth.py — run this ONCE on your PC to regenerate token.json
for YOUTUBE UPLOAD permissions.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

print("=== AUTHORIZING YOUTUBE ===")
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/youtube.upload']
)
creds = flow.run_local_server(port=0)

with open('token.json', 'w') as f:
    f.write(creds.to_json())

print("\nSUCCESS — copy everything below this line into your YOUTUBE_TOKEN_JSON secret:")
print(open('token.json').read())