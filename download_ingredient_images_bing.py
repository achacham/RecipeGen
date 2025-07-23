import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time

# ✅ Use this path to your working ingredient list
INGREDIENTS = [
    "arborio rice", "black pepper", "butternut squash", "chili flakes", "cream",
    "eggs", "garlic", "mushrooms", "onion", "pancetta", "parmesan", "parsley",
    "penne", "spaghetti"
]

# ✅ Output folder for images
out_dir = os.path.join("static", "images", "ingredients")
os.makedirs(out_dir, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_first_bing_image(query):
    try:
        url = f"https://www.bing.com/images/search?q={quote(query)}&form=HDRSC2"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        img_tag = soup.find("img", {"class": "mimg"})
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
    except Exception as e:
        print(f"❌ Error for '{query}': {e}")
    return None

# 🔁 Main loop
for ingr in sorted(set(INGREDIENTS)):
    safe = ingr.replace(" ", "_")
    filename = f"{safe}.jpg"
    path = os.path.join(out_dir, filename)

    if os.path.exists(path):
        print(f"✅ Skipping '{ingr}', already exists.")
        continue

    print(f"🔍 Searching Bing for '{ingr}'...")
    img_url = fetch_first_bing_image(ingr)

    if not img_url:
        print(f"⚠️ Could not fetch image for '{ingr}'")
        continue

    try:
        img_resp = requests.get(img_url, headers=HEADERS, timeout=10)
        if img_resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(img_resp.content)
            print(f"📥 Saved image for '{ingr}'")
        else:
            print(f"⚠️ Failed to download image content for '{ingr}'")
    except Exception as e:
        print(f"❌ Download error for '{ingr}': {e}")

    time.sleep(1.5)  # polite pause

print("🎉 Done. All images attempted.")
