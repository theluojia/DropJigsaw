#!/usr/bin/env python3
"""add_images.py - Fill images/ to TARGET count. Sources: loremflickr, picsum, pixabay"""

import os, sys, urllib.request, urllib.error, time, random, io, ssl, json

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
TARGET = 400
TW, TH = 400, 600

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def existing_nums():
    if not os.path.exists(IMAGES_DIR): return set()
    return {int(f.replace(".jpg","")) for f in os.listdir(IMAGES_DIR) if f.endswith(".jpg")}

def missing_nums():
    have = existing_nums()
    return sorted([i for i in range(1, TARGET+1) if i not in have])

def download_one(url, path, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            resp = urllib.request.urlopen(req, timeout=20, context=SSL_CTX)
            data = resp.read()
            if len(data) < 1000: raise Exception("Too small")
            from PIL import Image
            img = Image.open(io.BytesIO(data)).convert("RGB")
            w, h = img.size
            ratio = TW / TH
            if w / h > ratio:
                nw = int(h * ratio)
                img = img.crop(((w-nw)//2, 0, (w-nw)//2+nw, h))
            else:
                nh = int(w / ratio)
                img = img.crop((0, (h-nh)//2, w, (h-nh)//2+nh))
            img = img.resize((TW, TH), Image.LANCZOS)
            img.save(path, "JPEG", quality=82, optimize=True)
            return True
        except Exception as e:
            if attempt < retries - 1: time.sleep(1 + attempt * 2)
    return False

def fill_from_pixabay(missing, api_key=None):
    """Pixabay illustrations + vectors search"""
    if not api_key: return 0
    done = 0
    categories = ["illustration","vector","art","nature","abstract"]
    for idx in missing:
        if done >= len(missing): break
        path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
        if os.path.exists(path): done += 1; continue
        cat = categories[idx % len(categories)]
        url = f"https://pixabay.com/api/?key={api_key}&q={cat}&orientation=vertical&image_type=illustration&per_page=3&page={random.randint(1,10)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.loads(urllib.request.urlopen(req, timeout=15, context=SSL_CTX).read())
            for hit in data.get("hits",[]):
                img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                if img_url and download_one(img_url, path):
                    done += 1
                    if done % 10 == 0: print(f"  pixabay: {done}")
                    break
        except: pass
        time.sleep(0.5)
    return done

def fill_from_loremflickr(missing):
    done = 0
    categories = ["nature","portrait","art","people","city","abstract","food","travel","architecture","fashion"]
    for idx in missing:
        path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
        if os.path.exists(path): done += 1; continue
        cat = categories[idx % len(categories)]
        url = f"https://loremflickr.com/{TW}/{TH}/{cat}?random={idx}"
        if download_one(url, path):
            done += 1
            if done % 20 == 0: print(f"  loremflickr: {done}")
        time.sleep(0.25)
    return done

def fill_from_picsum(missing):
    done = 0
    for idx in missing:
        path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
        if os.path.exists(path): done += 1; continue
        seed = idx * 137 + 42
        url = f"https://picsum.photos/seed/{seed}/{TW}/{TH}"
        if download_one(url, path):
            done += 1
            if done % 10 == 0: print(f"  picsum: {done}")
        time.sleep(0.2)
    return done

def main():
    missing = missing_nums()
    print(f"Have: {len(existing_nums())}, need: {len(missing)} for target {TARGET}")
    if not missing: print("Already at target!"); return

    pixabay_key = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--pixabay" and i+1 < len(args): pixabay_key = args[i+1]

    if pixabay_key:
        got = fill_from_pixabay(missing, pixabay_key)
        print(f"Pixabay: {got}")
    
    missing = missing_nums()
    if missing:
        print("Trying loremflickr...")
        fill_from_loremflickr(missing)
    
    missing = missing_nums()
    if missing:
        print("Trying picsum...")
        fill_from_picsum(missing)
    
    print(f"Final: {len(existing_nums())}")

if __name__ == "__main__":
    main()
