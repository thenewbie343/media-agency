import os
import requests
from ddgs import DDGS

def download_images():
    query = "kiara advani war 2 bikini"
    assets_dir = os.path.join("assets", "kiara_advani_war2")
    os.makedirs(assets_dir, exist_ok=True)
    
    print(f"[*] Searching DuckDuckGo (via ddgs) for: {query}")
    try:
        results = list(DDGS().images(query, max_results=5))
        
        for i, result in enumerate(results):
            image_url = result.get("image")
            if not image_url:
                continue
                
            print(f"[*] Downloading {i+1}/5: {image_url}")
            try:
                # Add a User-Agent to avoid getting blocked by the image host
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(image_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    file_path = os.path.join(assets_dir, f"photo_{i+1}.jpg")
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                    print(f"  -> Saved to {file_path}")
                else:
                    print(f"  [!] Failed to download, status: {resp.status_code}")
            except Exception as e:
                print(f"  [!] Request failed: {e}")
                
    except Exception as e:
        print(f"[!] Search failed: {e}")

if __name__ == "__main__":
    download_images()
