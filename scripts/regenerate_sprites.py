#!/usr/bin/env python3
"""Regenerate emotion sprite sheets - force correct tiny pixel art size."""

import base64
import json
import os
import sys
import time
import urllib.request
from PIL import Image
from io import BytesIO

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

ASSETS_DIR = "notchi/notchi/Assets.xcassets"

CHAR_DESC = """This is TINY retro pixel art. The character is only about 24 pixels wide and 28 pixels tall.
- Body: simple rounded rectangle, warm orange (#E87040) with 1px darker outline
- 4 tiny stubby legs (just 2-3 pixels each)
- Face: 2 single-pixel black dot eyes, tiny 2-3 pixel mouth
- VERY low detail - this is 8-bit style with minimal pixels
- Each animation frame is exactly 64x64 pixels with transparent background
- The character takes up roughly the center-bottom of each 64x64 frame"""

TASKS = {
    "idle": {
        "ref": "idle_neutral",
        "frames": 6,
        "width": 384,
        "desc": "standing upright, subtle idle sway between frames",
    },
    "working": {
        "ref": "working_neutral",
        "frames": 6,
        "width": 384,
        "desc": "standing with a tiny white speech bubble above head",
    },
    "waiting": {
        "ref": "waiting_neutral",
        "frames": 6,
        "width": 384,
        "desc": "standing with a tiny red ! mark above head",
    },
    "sleeping": {
        "ref": "sleeping_neutral",
        "frames": 6,
        "width": 384,
        "desc": "lying flat/horizontal with Z letters floating above",
    },
    "compacting": {
        "ref": "compacting_neutral",
        "frames": 5,
        "width": 320,
        "desc": "shrinking from large to tiny size across frames",
    },
}

EMOTIONS = {
    "excited": "star eyes (two ★ shapes replacing dot eyes), wide open smiling mouth (3-4px), the character is slightly lifted/jumping in some frames",
    "angry": "V-shaped angry eyebrows (2px lines above eyes), jagged frown mouth, slightly darker/redder tint on top of head",
    "love": "heart-shaped eyes (two tiny ♥ replacing dot eyes), small curved smile, tiny pink blush dots on cheeks, one small heart floating above",
}


def load_reference_image(name: str) -> str:
    path = os.path.join(ASSETS_DIR, f"{name}.imageset", "sprite_sheet.png")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate_sprite(task_name: str, emotion_name: str) -> bool:
    task = TASKS[task_name]
    emotion_desc = EMOTIONS[emotion_name]
    ref_b64 = load_reference_image(task["ref"])
    target_w = task["width"]
    target_h = 64
    frames = task["frames"]

    output_name = f"{task_name}_{emotion_name}"
    output_dir = os.path.join(ASSETS_DIR, f"{output_name}.imageset")

    prompt = f"""Look at this reference sprite sheet. I need you to create a new one in the EXACT same style.

REFERENCE: A {target_w}x{target_h} pixel sprite sheet with {frames} frames of 64x64 each, laid out horizontally. It shows a tiny orange blob creature: {task['desc']}.

{CHAR_DESC}

CREATE: A new sprite sheet keeping the EXACT same character, poses, animation, and pixel art style. The ONLY change is the facial expression:

Emotion "{emotion_name}": {emotion_desc}

CRITICAL - THIS IS TINY PIXEL ART:
- Output MUST be exactly {target_w}x{target_h} pixels total
- Each frame is 64x64 pixels, {frames} frames side by side horizontally
- The character is TINY (24x28 px) - use MINIMAL pixels for features
- NO anti-aliasing, NO gradients, NO smooth edges - pure sharp pixel art
- Transparent background
- Keep the SAME orange color (#E87040), same body shape, same legs
- Eyes are only 1-2 pixels each, mouth is 2-4 pixels
- Match the reference's level of simplicity exactly"""

    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{ref_b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "modalities": ["image", "text"],
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ✗ {output_name}: API error - {e}")
        return False

    choices = result.get("choices", [])
    if not choices:
        print(f"  ✗ {output_name}: no choices")
        return False

    message = choices[0].get("message", {})
    images = message.get("images", [])

    img_data = None
    if images:
        img_url = images[0].get("image_url", {}).get("url", "")
        if img_url.startswith("data:image"):
            b64_data = img_url.split(",", 1)[1]
            img_data = base64.b64decode(b64_data)
    else:
        import re
        content = message.get("content", "")
        match = re.search(r'data:image/\w+;base64,([A-Za-z0-9+/=]+)', content)
        if match:
            img_data = base64.b64decode(match.group(1))

    if not img_data:
        print(f"  ✗ {output_name}: no image in response")
        return False

    # Resize to exact dimensions using nearest-neighbor
    img = Image.open(BytesIO(img_data))
    img = img.resize((target_w, target_h), Image.NEAREST)

    os.makedirs(output_dir, exist_ok=True)
    img.save(os.path.join(output_dir, "sprite_sheet.png"), "PNG")

    contents = {
        "images": [{"filename": "sprite_sheet.png", "idiom": "universal"}],
        "info": {"author": "xcode", "version": 1},
        "properties": {"preserves-vector-representation": False},
    }
    with open(os.path.join(output_dir, "Contents.json"), "w") as f:
        json.dump(contents, f, indent=2)

    # Verify
    verify = Image.open(os.path.join(output_dir, "sprite_sheet.png"))
    print(f"  ✓ {output_name} saved ({verify.size[0]}x{verify.size[1]})")
    return True


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    total = 0
    success = 0

    for task_name in TASKS:
        print(f"\n[{task_name}]")
        for emotion_name in EMOTIONS:
            total += 1
            print(f"  Generating {task_name}_{emotion_name}...")
            if generate_sprite(task_name, emotion_name):
                success += 1
            time.sleep(2)

    print(f"\nDone: {success}/{total}")


if __name__ == "__main__":
    main()
