#!/usr/bin/env python3
"""add_images.py - Download portrait images. Fills gaps to reach 300."""

import os, sys, urllib.request, urllib.error, time, random, io, ssl

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
TARGET = 300
TW, TH = 400, 600

# Unverified SSL context for stubborn servers
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def existing_nums():
    if not os.path.exists(IMAGES_DIR):
        return set()
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
            if len(data) < 1000:
                raise Exception("Too small")
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
            if attempt < retries - 1:
                time.sleep(1 + attempt * 2)
            else:
                pass
    return False

def fill_from_picsum(missing):
    """Use picsum.photos"""
    done = 0
    for idx in missing:
        path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
        if os.path.exists(path):
            done += 1; continue
        seed = idx * 137 + 42
        url = f"https://picsum.photos/seed/{seed}/{TW}/{TH}"
        if download_one(url, path):
            done += 1
            if done % 10 == 0: print(f"  picsum: {done}")
        else:
            print(f"  picsum FAIL {idx}")
        time.sleep(0.2)
    return done

def fill_from_loremflickr(missing):
    """Use loremflickr.com"""
    done = 0
    categories = ["nature","portrait","art","people","city","abstract","food","travel"]
    for idx in missing:
        path = os.path.join(IMAGES_DIR, f"{idx}.jpg")
        if os.path.exists(path):
            done += 1; continue
        cat = categories[idx % len(categories)]
        url = f"https://loremflickr.com/{TW}/{TH}/{cat}?random={idx}"
        if download_one(url, path):
            done += 1
            if done % 10 == 0: print(f"  loremflickr: {done}")
        time.sleep(0.3)
    return done

def main():
    missing = missing_nums()
    print(f"Total images: {len(existing_nums())}, need: {len(missing)}")
    if not missing:
        print("Already have 300!")
        return

    # Try loremflickr first
    print("Trying loremflickr...")
    got = fill_from_loremflickr(missing)
    
    missing = missing_nums()
    if missing:
        print(f"Still need {len(missing)}, trying picsum...")
        got2 = fill_from_picsum(missing)
    
    print(f"Final count: {len(existing_nums())}")

if __name__ == "__main__":
    main()
