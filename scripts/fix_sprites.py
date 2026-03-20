#!/usr/bin/env python3
"""Fix specific sprite sheets with better prompts."""

import base64, json, os, re, time, urllib.request
from PIL import Image
from io import BytesIO

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
ASSETS = "notchi/notchi/Assets.xcassets"

CHAR = """The character is a tiny cute orange rectangular blob in retro pixel art.
- Body: rounded rectangle, color #E87040, 1px darker outline, 1px black border
- About 24x28 pixels in a 64x64 transparent canvas
- 4 small stubby dark orange legs at bottom
- VERY simple - minimal pixels, 8-bit style, NO anti-aliasing, NO gradients
- Sharp pixel edges only"""

FIXES = [
    # Excited - cuter eyes (use happy eyes with small sparkle marks, not weird star eyes)
    {
        "name": "idle_excited",
        "ref": "idle_happy",
        "frames": 6, "width": 384,
        "emotion": "Keep the SAME happy smiling face as the reference. Add only: two tiny 1-pixel yellow sparkle dots near the eyes (one on each side). The character looks very happy and energetic. Keep the same poses and animation as reference.",
    },
    {
        "name": "working_excited",
        "ref": "working_neutral",
        "frames": 6, "width": 384,
        "emotion": "Same happy face with tiny sparkle dots near eyes. IMPORTANT: Keep the WHITE speech/thought bubble above the head exactly as in the reference - the bubble must have a solid WHITE background, not transparent. Same poses as reference.",
    },
    {
        "name": "sleeping_excited",
        "ref": "sleeping_neutral",
        "frames": 6, "width": 384,
        "emotion": "The character is lying FLAT as a horizontal SQUARE/RECTANGLE shape (NOT round). Same as reference but with a small smile. Keep the Z speech bubbles above. The body is a flat horizontal rectangle, NOT a circle or rounded blob.",
    },
    # Angry - fix idle consistency, sleeping shape, compacting background, working bubble
    {
        "name": "idle_angry",
        "ref": "idle_neutral",
        "frames": 6, "width": 384,
        "emotion": "Angry face: V-shaped eyebrows (2px lines above the dot eyes), small frown mouth. ALL 6 frames must show the SAME character with the SAME face, SAME size, SAME proportions. Only subtle idle sway animation between frames - do NOT change the face or body between frames.",
    },
    {
        "name": "working_angry",
        "ref": "working_neutral",
        "frames": 6, "width": 384,
        "emotion": "Angry face: V-shaped eyebrows, small frown mouth. IMPORTANT: Keep the WHITE speech/thought bubble above the head exactly as in the reference - the bubble must have a solid WHITE background. Same poses as reference.",
    },
    {
        "name": "sleeping_angry",
        "ref": "sleeping_neutral",
        "frames": 6, "width": 384,
        "emotion": "The character is lying FLAT as a horizontal SQUARE/RECTANGLE shape (NOT round, NOT circular). Exactly like the reference sleeping sprite. Same flat rectangular body. Same Z speech bubbles above. The only change: add small V-shaped angry eyebrows above the closed eyes.",
    },
    {
        "name": "compacting_angry",
        "ref": "compacting_neutral",
        "frames": 5, "width": 320,
        "emotion": "Angry face: V-shaped eyebrows, small frown. Same shrinking animation as reference. CRITICAL: The background MUST be completely transparent - NO white pixels, NO gray pixels, NO checkered pattern. Only the orange character should have color.",
    },
    # Love - fix sleeping shape, working bubble
    {
        "name": "working_love",
        "ref": "working_neutral",
        "frames": 6, "width": 384,
        "emotion": "Same normal dot eyes but with tiny pink blush dots on cheeks, small smile. A tiny pink heart above. IMPORTANT: Keep the WHITE speech/thought bubble above the head exactly as in the reference - the bubble must have a solid WHITE background. Same poses as reference.",
    },
    {
        "name": "sleeping_love",
        "ref": "sleeping_neutral",
        "frames": 6, "width": 384,
        "emotion": "The character is lying FLAT as a horizontal SQUARE/RECTANGLE shape (NOT round, NOT circular). Exactly like the reference sleeping sprite. Same flat rectangular body. Same Z speech bubbles above. The only change: add tiny pink blush dots on cheeks and a small heart floating above.",
    },
]


def load_ref(name):
    path = f"{ASSETS}/{name}.imageset/sprite_sheet.png"
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate(fix):
    name = fix["name"]
    ref_b64 = load_ref(fix["ref"])
    w, h, frames = fix["width"], 64, fix["frames"]

    prompt = f"""Look at this reference sprite sheet carefully. Create a new one in the EXACT same pixel art style.

REFERENCE: A {w}x{h} pixel sprite sheet with {frames} frames of 64x64 each in a horizontal strip.

{CHAR}

CHANGES: {fix["emotion"]}

CRITICAL RULES:
1. Output EXACTLY {w}x{h} pixels - {frames} frames of 64x64 side by side
2. Keep SAME orange color (#E87040), same body shape, same stubby legs
3. NO anti-aliasing, NO gradients - pure sharp pixel art
4. TRANSPARENT background - absolutely NO white, gray, or any background color
5. Match the reference's character size and position in each frame
6. All frames must be consistent - same character, same proportions"""

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
        return False

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
        return False

    img = Image.open(BytesIO(img_data)).convert("RGBA")
    img = img.resize((w, h), Image.NEAREST)

    # Remove background
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r > 180 and g > 180 and b > 180:
                pixels[x, y] = (0, 0, 0, 0)

    out_dir = f"{ASSETS}/{name}.imageset"
    os.makedirs(out_dir, exist_ok=True)
    img.save(f"{out_dir}/sprite_sheet.png", "PNG")
    print(f"  ✓ {name}")
    return True


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set")
        return

    for fix in FIXES:
        print(f"  Generating {fix['name']}...")
        generate(fix)
        time.sleep(2)

    print("\nDone")


if __name__ == "__main__":
    main()
