#!/usr/bin/env python3
"""Regenerate all 3 sleeping emotion sprites with proper bg removal."""

import base64, json, os, re, time, urllib.request
from PIL import Image
from io import BytesIO
from collections import deque

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
ASSETS = "notchi/notchi/Assets.xcassets"


def load_ref(name):
    with open(f"{ASSETS}/{name}.imageset/sprite_sheet.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def clean_background(img):
    """Two-pass: flood-fill from edges (safe), then remove isolated gray not near character."""
    pixels = img.load()
    w, h = img.size

    # Pass 1: flood-fill from edges, stop at dark pixels (outlines)
    visited = set()
    queue = deque()
    for x in range(w):
        queue.append((x, 0))
        queue.append((x, h - 1))
    for y in range(h):
        queue.append((0, y))
        queue.append((w - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or x >= w or y < 0 or y >= h:
            continue
        visited.add((x, y))
        r, g, b, a = pixels[x, y]
        if a == 0:
            # Already transparent, but keep spreading
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited:
                        queue.append((nx, ny))
            continue
        # Light pixel (background or white bubble fill) reachable from edge = background
        if r > 140 and g > 140 and b > 140:
            pixels[x, y] = (0, 0, 0, 0)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited:
                        queue.append((nx, ny))
        # Dark pixel = outline boundary, don't spread through it


def generate(name, ref_name, emotion_desc):
    ref_b64 = load_ref(ref_name)

    prompt = f"""Look at this reference sprite sheet. Create a new one in the EXACT same style.

REFERENCE: 384x64 pixel sprite sheet, 6 frames of 64x64. The character is lying FLAT as a horizontal RECTANGLE with white Z speech bubbles above. The Z bubbles have a solid WHITE background enclosed by dark outlines. The face is facing slightly left.

The character is a tiny cute orange rectangular blob in retro pixel art.
- Body: flat horizontal RECTANGLE, color #E87040, 1px darker outline
- VERY simple 8-bit pixel art, NO anti-aliasing
- Each frame is 64x64 with transparent background

CHANGES: {emotion_desc}

CRITICAL:
1. EXACTLY 384x64 pixels - 6 frames of 64x64
2. Flat horizontal RECTANGLE body (NOT round)
3. Z speech bubbles MUST have solid WHITE fill enclosed by dark outline
4. Transparent background EXCEPT white Z bubbles
5. Uniform orange #E87040 body color
6. Progressive Z's across frames"""

    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_b64}"}},
            {"type": "text", "text": prompt},
        ]}],
        "modalities": ["image", "text"],
        "max_tokens": 1024,
    }

    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return

    msg = result.get("choices", [{}])[0].get("message", {})
    images = msg.get("images", [])
    img_data = None
    if images:
        url = images[0].get("image_url", {}).get("url", "")
        if url.startswith("data:image"):
            img_data = base64.b64decode(url.split(",", 1)[1])
    else:
        match = re.search(r'data:image/\w+;base64,([A-Za-z0-9+/=]+)', msg.get("content", ""))
        if match:
            img_data = base64.b64decode(match.group(1))

    if not img_data:
        print(f"  ✗ {name}: no image")
        return

    img = Image.open(BytesIO(img_data)).convert("RGBA")
    img = img.resize((384, 64), Image.NEAREST)
    clean_background(img)

    out_dir = f"{ASSETS}/{name}.imageset"
    os.makedirs(out_dir, exist_ok=True)
    img.save(f"{out_dir}/sprite_sheet.png", "PNG")
    print(f"  ✓ {name}")


fixes = [
    ("sleeping_excited", "sleeping_happy", "Happy sleeping with small smile. Same flat body, same Z bubbles with WHITE fill."),
    ("sleeping_angry", "sleeping_neutral", "Angry sleeping with V-shaped eyebrows. Same flat body, same Z bubbles with WHITE fill."),
    ("sleeping_love", "sleeping_neutral", "Sleeping with tiny pink blush on cheeks, small heart near Z bubble. Same flat body, same Z bubbles with WHITE fill."),
]

for name, ref, desc in fixes:
    print(f"  Generating {name}...")
    generate(name, ref, desc)
    time.sleep(2)

print("Done")
