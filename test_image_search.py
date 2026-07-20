import os
import requests
from duckduckgo_search import DDGS

def test_image_search():
    query = "ISRO Chandrayaan 3 launch high quality"
    assets_dir = os.path.join("assets", "test_images")
    os.makedirs(assets_dir, exist_ok=True)
    
    print(f"[*] Searching DuckDuckGo for: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5))
            
            for i, result in enumerate(results):
                image_url = result.get("image")
                if not image_url:
                    continue
                    
                print(f"[*] Downloading {i+1}/5: {image_url}")
                try:
                    resp = requests.get(image_url, timeout=10)
                    if resp.status_code == 200:
                        file_path = os.path.join(assets_dir, f"test_image_{i+1}.jpg")
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
    test_image_search()
