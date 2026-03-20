#!/usr/bin/env python3
"""Fix waiting_excited, sleeping_excited, sleeping_love."""

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
        if r > 130 and g > 130 and b > 130 and a > 0:
            pixels[x, y] = (0, 0, 0, 0)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited:
                        queue.append((nx, ny))


def remove_gray(img):
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if 100 < r < 170 and 100 < g < 170 and 100 < b < 170 and abs(r-g) < 15 and abs(g-b) < 15:
                pixels[x, y] = (0, 0, 0, 0)


def generate(name, ref_name, width, frames, prompt_text):
    ref_b64 = load_ref(ref_name)

    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_b64}"}},
            {"type": "text", "text": prompt_text},
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
    img = img.resize((width, 64), Image.NEAREST)
    flood_fill_remove_bg(img)
    remove_gray(img)

    out_dir = f"{ASSETS}/{name}.imageset"
    os.makedirs(out_dir, exist_ok=True)
    img.save(f"{out_dir}/sprite_sheet.png", "PNG")
    print(f"  ✓ {name}")


CHAR = """The character is a tiny cute orange rectangular blob in retro pixel art.
- Body: SQUARE/RECTANGULAR shape (NOT round, NOT circular), color #E87040
- 1px darker outline, 4 small stubby dark orange legs
- About 24x28 pixels in a 64x64 frame
- VERY simple 8-bit pixel art, NO anti-aliasing"""

# 1. waiting_excited - use waiting_neutral as reference, keep square shape
print("  Generating waiting_excited...")
generate("waiting_excited", "waiting_neutral", 384, 6, f"""Look at this reference sprite sheet. Create a new one in the EXACT same style.

REFERENCE: 384x64 pixel sprite sheet, 6 frames of 64x64. The character is standing upright as a SQUARE/RECTANGULAR body (NOT round) with a red ! mark above its head.

{CHAR}

CHANGES: Keep the exact same SQUARE body shape and red ! mark as reference. Add a small happy smile mouth. That's the only change.

CRITICAL:
1. EXACTLY 384x64 pixels - 6 frames of 64x64
2. Body must be SQUARE/RECTANGULAR - NOT round or circular - match the reference shape exactly
3. Keep the red ! mark above head
4. Transparent background
5. All frames consistent""")

time.sleep(2)

# 2. sleeping_excited - use sleeping_happy as ref, face slightly left
print("  Generating sleeping_excited...")
generate("sleeping_excited", "sleeping_happy", 384, 6, f"""Look at this reference sprite sheet. Create a new one in the EXACT same style.

REFERENCE: 384x64 pixel sprite sheet, 6 frames of 64x64. The character is lying FLAT as a horizontal rectangle with white Z speech bubbles above. The character's face is facing slightly to the LEFT (not forward/centered).

{CHAR}

CHANGES: Keep EXACTLY the same pose, same flat rectangular body, same face direction (slightly left), same Z bubbles with WHITE fill. Add a small happy smile. That's the only change.

CRITICAL:
1. EXACTLY 384x64 pixels - 6 frames of 64x64
2. Body is FLAT horizontal rectangle, face looking slightly LEFT like the reference
3. Z speech bubbles must have solid WHITE fill
4. Transparent background
5. Same orange color #E87040 uniformly across the entire body - no dark spots""")

time.sleep(2)

# 3. sleeping_love - fix dark spot on top right
print("  Generating sleeping_love...")
generate("sleeping_love", "sleeping_happy", 384, 6, f"""Look at this reference sprite sheet. Create a new one in the EXACT same style.

REFERENCE: 384x64 pixel sprite sheet, 6 frames of 64x64. The character is lying FLAT as a horizontal rectangle with white Z speech bubbles above. The character's face is facing slightly to the LEFT.

{CHAR}

CHANGES: Keep EXACTLY the same pose, flat body, face direction. Add tiny pink blush dots on cheeks and a small heart near the Z bubble.

CRITICAL:
1. EXACTLY 384x64 pixels - 6 frames of 64x64
2. Body is FLAT horizontal rectangle
3. The ENTIRE body must be uniform orange #E87040 - NO dark patches, NO shadow, NO color variation on the body
4. Z speech bubbles must have solid WHITE fill
5. Transparent background
6. Same orange color everywhere on the body""")

print("Done")
