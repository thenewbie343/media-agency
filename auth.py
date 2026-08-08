"""
auth.py — run this ONCE on your PC to regenerate token.json
with BOTH YouTube upload AND Google Drive permissions.

If you already have a token.json from before, this REPLACES it
with a wider-permission version. You must redo this because Google
requires a fresh consent when you add new scopes to a token.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

print("=== STEP 1/2: AUTHORIZE YOUTUBE ===")
print("Your browser will open. Please grant YouTube upload permissions.")
flow1 = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/youtube.upload']
)
creds1 = flow1.run_local_server(port=0)

print("\n=== STEP 2/2: AUTHORIZE GOOGLE DRIVE ===")
print("Your browser will open again. Please check the box for Google Drive!")
print("(This two-step process bypasses Google's security rule preventing them from being requested together.)")
flow2 = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/drive.file']
)
# Passing include_granted_scopes='true' ensures the new token inherits the YouTube permissions!
creds2 = flow2.run_local_server(port=0, include_granted_scopes='true')

with open('token.json', 'w') as f:
    f.write(creds2.to_json())

print("\nSUCCESS — copy everything below this line into your YOUTUBE_TOKEN_JSON secret:")
print(open('token.json').read())