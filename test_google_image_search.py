import os
import requests
from bs4 import BeautifulSoup

def test_google_image_search():
    query = "kiara advani bikini"
    assets_dir = os.path.join("assets", "kiara_advani_bikini")
    os.makedirs(assets_dir, exist_ok=True)
    
    print(f"[*] Searching for: {query}")
    try:
        url = f"https://www.google.com/search?q={query}&tbm=isch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        images = soup.find_all('img')
        
        count = 0
        for i, img in enumerate(images):
            if count >= 5:
                break
                
            image_url = img.get('data-src') or img.get('src')
            if not image_url or not image_url.startswith('http'):
                continue
                
            print(f"[*] Downloading {count+1}/5: {image_url}")
            try:
                img_resp = requests.get(image_url, timeout=10)
                if img_resp.status_code == 200:
                    file_path = os.path.join(assets_dir, f"photo_{count+1}.jpg")
                    with open(file_path, "wb") as f:
                        f.write(img_resp.content)
                    print(f"  -> Saved to {file_path}")
                    count += 1
                else:
                    print(f"  [!] Failed to download, status: {img_resp.status_code}")
            except Exception as e:
                print(f"  [!] Request failed: {e}")
                
    except Exception as e:
        print(f"[!] Search failed: {e}")

if __name__ == "__main__":
    test_google_image_search()
