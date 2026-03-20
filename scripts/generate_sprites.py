#!/usr/bin/env python3
"""Generate emotion sprite sheets using OpenRouter's Nano Banana 2 model."""

import base64
import json
import os
import sys
import time
import urllib.request

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "google/gemini-3.1-flash-image-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

ASSETS_DIR = "notchi/notchi/Assets.xcassets"

# Character description for consistent style
CHAR_DESC = """The character is a tiny cute orange/coral colored rectangular blob creature in retro pixel art style.
- Body: rounded rectangle, main color #E87040 (warm orange) with darker #C05830 outline, 1-pixel black border
- Size: approximately 24x28 pixels within a 64x64 transparent canvas
- Has 4 small stubby dark orange legs at the bottom
- Face is on the front of the body: 2 small black dot eyes and a small mouth
- Transparent/clear background (no background color)
- Clean pixel art with no anti-aliasing, sharp edges"""

TASKS = {
    "idle": {
        "ref": "idle_neutral",
        "frames": 6,
        "desc": "standing upright with subtle idle animation (slight body shift between frames)",
        "size": "384x64",
    },
    "working": {
        "ref": "working_neutral",
        "frames": 6,
        "desc": "standing with a small white speech/thought bubble above its head, typing animation",
        "size": "384x64",
    },
    "waiting": {
        "ref": "waiting_neutral",
        "frames": 6,
        "desc": "standing with a small red exclamation mark (!) in a circle above its head",
        "size": "384x64",
    },
    "sleeping": {
        "ref": "sleeping_neutral",
        "frames": 6,
        "desc": "lying flat/horizontal with Z letters in speech bubbles floating above, progressively more Z's across frames",
        "size": "384x64",
    },
    "compacting": {
        "ref": "compacting_neutral",
        "frames": 5,
        "desc": "shrinking animation sequence from large to tiny and back to large",
        "size": "320x64",
    },
}

EMOTIONS = {
    "excited": "star-shaped eyes (★) or wide sparkling eyes, wide open mouth in a big grin, slightly jumping/bouncing pose, radiating energy lines around the body",
    "angry": "angry V-shaped eyebrows drawn above eyes, gritted teeth or jagged frown mouth, slight red tint on top of head like steaming, tense/rigid body posture",
    "love": "heart-shaped eyes (♥), rosy pink circles on cheeks (blush), small happy curved smile, dreamy relaxed posture, a tiny floating heart above head",
}


def load_reference_image(name: str) -> str:
    """Load a sprite sheet PNG and return base64 string."""
    path = os.path.join(ASSETS_DIR, f"{name}.imageset", "sprite_sheet.png")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate_sprite(task_name: str, emotion_name: str) -> bool:
    """Generate a single sprite sheet."""
    task = TASKS[task_name]
    emotion_desc = EMOTIONS[emotion_name]
    ref_b64 = load_reference_image(task["ref"])

    output_name = f"{task_name}_{emotion_name}"
    output_dir = os.path.join(ASSETS_DIR, f"{output_name}.imageset")

    if os.path.exists(os.path.join(output_dir, "sprite_sheet.png")):
        print(f"  ⏭ {output_name} already exists, skipping")
        return True

    prompt = f"""Look at this reference pixel art sprite sheet carefully. I need you to generate a NEW sprite sheet in the EXACT SAME pixel art style, character design, and dimensions.

REFERENCE IMAGE: This is a {task['size']} pixel sprite sheet of a cute orange blob creature. It contains {task['frames']} animation frames laid out horizontally, each frame is 64x64 pixels. The character is {task['desc']}.

{CHAR_DESC}

YOUR TASK: Generate a new {task['size']} pixel sprite sheet with {task['frames']} frames (each 64x64), keeping the EXACT same character design, orange color (#E87040), pixel art style, body shape, and animation poses as the reference.

THE ONLY CHANGE: Modify the character's facial expression and minor body language to show the "{emotion_name}" emotion:
{emotion_desc}

CRITICAL RULES:
1. Output image must be EXACTLY {task['size']} pixels - {task['frames']} frames of 64x64 each in a single horizontal strip
2. Keep the SAME orange body color, dark outline, stubby legs, and overall shape
3. Keep the SAME animation poses/sequence as the reference - only change the face/expression
4. Use clean pixel art with no anti-aliasing, no gradients, sharp pixel edges
5. Transparent background (no background fill)
6. The character should be roughly the same size in each frame as the reference
7. Match the reference's pixel density and detail level exactly"""

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

    # Extract image from response
    choices = result.get("choices", [])
    if not choices:
        print(f"  ✗ {output_name}: no choices in response")
        return False

    message = choices[0].get("message", {})
    images = message.get("images", [])

    if not images:
        # Sometimes the image is inline in content as a data URL
        content = message.get("content", "")
        if "data:image" in content:
            import re
            match = re.search(r'data:image/\w+;base64,([A-Za-z0-9+/=]+)', content)
            if match:
                img_data = base64.b64decode(match.group(1))
                save_sprite(output_dir, output_name, img_data)
                return True
        print(f"  ✗ {output_name}: no images in response")
        if content:
            print(f"    Response text: {content[:200]}")
        return False

    img_url = images[0].get("image_url", {}).get("url", "")
    if not img_url.startswith("data:image"):
        print(f"  ✗ {output_name}: unexpected image format")
        return False

    # Decode base64 image
    b64_data = img_url.split(",", 1)[1]
    img_data = base64.b64decode(b64_data)

    save_sprite(output_dir, output_name, img_data)
    return True


def save_sprite(output_dir: str, name: str, img_data: bytes):
    """Save sprite sheet to asset catalog."""
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "sprite_sheet.png"), "wb") as f:
        f.write(img_data)

    contents = {
        "images": [{"filename": "sprite_sheet.png", "idiom": "universal"}],
        "info": {"author": "xcode", "version": 1},
        "properties": {"preserves-vector-representation": False},
    }
    with open(os.path.join(output_dir, "Contents.json"), "w") as f:
        json.dump(contents, f, indent=2)

    print(f"  ✓ {name} saved")


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
            time.sleep(2)  # Rate limit

    print(f"\nDone: {success}/{total} sprite sheets generated")


if __name__ == "__main__":
    main()
