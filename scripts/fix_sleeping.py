#!/usr/bin/env python3
"""Fix sleeping sprites - transparent bg + preserve white Z bubble."""

import base64, json, os, re, time, urllib.request
from PIL import Image
from io import BytesIO
from collections import deque

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
ASSETS = "notchi/notchi/Assets.xcassets"

CHAR = """The character is a tiny cute orange rectangular blob in retro pixel art.
- Body: flat horizontal RECTANGLE (NOT round), color #E87040, 1px darker outline
- The sleeping character lies FLAT like a horizontal bar/plank
- VERY simple - minimal pixels, 8-bit style, NO anti-aliasing
- Each frame is 64x64 with transparent background"""


def load_ref(name):
    with open(f"{ASSETS}/{name}.imageset/sprite_sheet.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def flood_fill_remove_bg(img):
    pixels = img.load()
    w, h = img.size
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
        if r > 180 and g > 180 and b > 180 and a > 0:
            pixels[x, y] = (0, 0, 0, 0)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    queue.append((nx, ny))


def generate(name, emotion_desc):
    ref_b64 = load_ref("sleeping_neutral")

    prompt = f"""Look at this reference sprite sheet. Create a new one in the EXACT same style.

REFERENCE: 384x64 pixel sprite sheet, 6 frames of 64x64 each. The character is lying FLAT as a horizontal rectangle (like a plank) with WHITE Z-letter speech bubbles floating above. The Z bubbles have solid WHITE backgrounds with dark outlines.

{CHAR}

CHANGES: {emotion_desc}

CRITICAL:
1. Output EXACTLY 384x64 pixels - 6 frames of 64x64
2. Character body must be a FLAT horizontal RECTANGLE - NOT round, NOT circular
3. The Z speech bubbles MUST have solid WHITE fill - do NOT make them transparent
4. Background must be transparent EXCEPT for the white Z bubbles
5. Keep same orange color, same flat lying pose as reference
6. All frames consistent, progressive Z's (Z, Z, ZZ, ZZ, ZZZ, ZZZ)"""

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
    flood_fill_remove_bg(img)

    out_dir = f"{ASSETS}/{name}.imageset"
    os.makedirs(out_dir, exist_ok=True)
    img.save(f"{out_dir}/sprite_sheet.png", "PNG")
    print(f"  ✓ {name}")


fixes = [
    ("sleeping_excited", "Happy sleeping face with small smile. Same flat rectangular body, same Z bubbles with white fill."),
    ("sleeping_angry", "Angry sleeping face with V-shaped eyebrows. Same flat rectangular body, same Z bubbles with white fill."),
    ("sleeping_love", "Sleeping face with tiny pink blush dots on cheeks, small heart near Z bubble. Same flat rectangular body, same Z bubbles with white fill."),
]

for name, desc in fixes:
    print(f"  Generating {name}...")
    generate(name, desc)
    time.sleep(2)

print("Done")
