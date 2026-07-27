#!/usr/bin/env python3
"""add_images.py - Fill images/ to TARGET count. Sources: unsplash (via loremflickr proxy), picsum"""

import os, sys, urllib.request, urllib.error, time, random, io, ssl
from collections import Counter

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
TARGET = 500
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

def is_too_monotonous(img):
    """Return True if image has very low color diversity."""
    try:
        from PIL import ImageStat
        stat = ImageStat.Stat(img)
        total_std = sum(stat.stddev)
        if total_std < 30:
            return True
        h = img.histogram()
        active = sum(1 for v in h if v > 0)
        if active / len(h) < 0.15:
            return True
        small = img.resize((40, 40))
        pixels = list(small.getdata())
        counts = Counter([(r//32, g//32, b//32) for (r, g, b) in pixels])
        if counts and counts.most_common(1)[0][1] / len(pixels) > 0.65:
            return True
    except:
        pass
    return False

def download_one(url, path, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            resp = urllib.request.urlopen(req, timeout=25, context=SSL_CTX)
            data = resp.read()
            if len(data) < 2000: raise Exception("Too small")
            from PIL import Image
            img = Image.open(io.BytesIO(data)).convert("RGB")
            if is_too_monotonous(img):
                print(f"  SKIP monotonous: {os.path.basename(path)}")
                return False
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
            print(f"  OK {os.path.basename(path)} ({w}x{h} -> {TW}x{TH})")
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 + attempt * 2)
    return False

def fill_from_loremflickr(missing):
    done = 0
    cats = ["nature","portrait","art","people","city","abstract","food","travel","architecture","fashion","animal","flower","mountain","ocean","night","sunset","forest","street","minimal"]
    for idx in missing:
        path = os.path.join(IMAGES_DIR, f"{idx:03d}.jpg")
        if os.path.exists(path):
            done += 1
            continue
        cat = cats[idx % len(cats)]
        # Use multiple urls for variety; loremflickr serves different images per random query
        urls = [
            f"https://loremflickr.com/{TW}/{TH}/{cat}?random={idx}",
        ]
        for url in urls:
            if download_one(url, path):
                done += 1
                if done % 10 == 0: print(f"  [loremflickr] progress: {done}")
                break
        time.sleep(0.3)
    return done

def fill_from_picsum(missing):
    done = 0
    for idx in missing:
        path = os.path.join(IMAGES_DIR, f"{idx:03d}.jpg")
        if os.path.exists(path):
            done += 1
            continue
        seed = idx * 137 + 42
        url = f"https://picsum.photos/seed/{seed}/{TW}/{TH}"
        if download_one(url, path):
            done += 1
            if done % 10 == 0: print(f"  [picsum] progress: {done}")
        time.sleep(0.25)
    return done

def main():
    missing = missing_nums()
    print(f"Have: {len(existing_nums())}, Missing: {len(missing)}, Target: {TARGET}")
    if not missing:
        print("Already at target!")
        return

    print("\n--- Phase 1: loremflickr (portrait + category variety) ---")
    fill_from_loremflickr(missing)

    missing = missing_nums()
    if missing:
        print(f"\n--- Phase 2: picsum ({len(missing)} remaining) ---")
        fill_from_picsum(missing)

    final = len(existing_nums())
    print(f"\n=== Done: {final}/{TARGET} images ===")
    if final < TARGET:
        print(f"Still missing {TARGET - final}. Re-run to fill gaps.")

if __name__ == "__main__":
    main()
