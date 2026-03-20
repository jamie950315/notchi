#!/usr/bin/env python3
"""Fix working sprites - preserve white speech bubble."""

import base64, json, os, re, time, urllib.request
from PIL import Image
from io import BytesIO
from collections import deque

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
ASSETS = "notchi/notchi/Assets.xcassets"

CHAR = """The character is a tiny cute orange rectangular blob in retro pixel art.
- Body: rounded rectangle, color #E87040, 1px darker outline
- About 24x28 pixels in a 64x64 transparent canvas
- 4 small stubby dark orange legs at bottom
- VERY simple - minimal pixels, 8-bit style, NO anti-aliasing"""


def load_ref(name):
    with open(f"{ASSETS}/{name}.imageset/sprite_sheet.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def flood_fill_remove_bg(img):
    """Remove background by flood-filling from edges. Preserves interior white (speech bubbles)."""
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
    ref_b64 = load_ref("working_neutral")

    prompt = f"""Look at this reference sprite sheet. Create a new one in the EXACT same style.

REFERENCE: 384x64 pixel sprite sheet, 6 frames of 64x64 each. Orange blob with a WHITE speech bubble above its head.

{CHAR}

CHANGES: {emotion_desc}

CRITICAL:
1. Output EXACTLY 384x64 pixels - 6 frames of 64x64
2. The speech bubble MUST have solid WHITE background - do NOT make it transparent
3. Keep same orange color, body shape, legs, poses
4. Pure pixel art, transparent background EXCEPT for the white speech bubble
5. All frames consistent"""

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
    ("working_excited", "Keep happy smiling face with tiny sparkle dots near eyes. The WHITE speech bubble above head must stay solid white."),
    ("working_angry", "Angry V-shaped eyebrows above dot eyes, small frown mouth. The WHITE speech bubble above head must stay solid white."),
    ("working_love", "Normal dot eyes with tiny pink blush on cheeks, small smile. The WHITE speech bubble above head must stay solid white."),
]

for name, desc in fixes:
    print(f"  Generating {name}...")
    generate(name, desc)
    time.sleep(2)

print("Done")
