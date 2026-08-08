"""
auth_drive.py — run this ONCE on your PC to generate drive_token.json
for GOOGLE DRIVE permissions.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

print("=== AUTHORIZING GOOGLE DRIVE ===")
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/drive.file']
)
creds = flow.run_local_server(port=0)

with open('drive_token.json', 'w') as f:
    f.write(creds.to_json())

print("\nSUCCESS — copy everything below this line into your DRIVE_TOKEN_JSON secret:")
print(open('drive_token.json').read())
