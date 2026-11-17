#!/usr/bin/env python3
"""flow2api.py — CLI for generating images and videos via a self-hosted Flow2API.

Flow2API exposes Google Flow (Veo / Gemini image models) as an
OpenAI-compatible API. This script is the execution layer of the
`flow2api-media` Hermes skill: it builds the request, streams the SSE
response, extracts the generated media URL, downloads the file locally,
and prints a JSON summary.

Authentication
--------------
The Flow2API API key is read ONLY from the environment:

    FLOW2API_API_KEY     (required for image/video/models)
    FLOW2API_BASE_URL    (optional, default https://flow2api.kevinny.tech)

Never hardcode the key in this file, in SKILL.md, or anywhere in the repo.

Usage
-----
    flow2api.py image --prompt "a cat astronaut" [--ar landscape] [--quality flash|pro|lite] [--size 2k|4k] [--ref img.png] [--out out.png]
    flow2api.py video --prompt "waves crashing" [--ar landscape|portrait] [--duration 4|6|8] [--quality fast|standard|lite|ultra|omni] [--image first.png] [--out out.mp4]
    flow2api.py models [--type image|video]
    flow2api.py health

Exit codes: 0 ok, 1 generation/API error, 2 configuration/usage error.
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT_BASE_URL = "https://flow2api.kevinny.tech"

# Overall request timeout (video generation can take several minutes).
REQUEST_TIMEOUT = 1800
# Per-read socket timeout; the SSE stream sends progress chunks regularly.
READ_TIMEOUT = 600

MARKDOWN_IMAGE_RE = re.compile(r"!\[.*?\]\((.*?)\)")
HTML_VIDEO_RE = re.compile(r"<video[^>]+src=['\"](.*?)['\"]", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Model catalog (matches flow2api MODEL_CONFIG at upstream HEAD)
# ---------------------------------------------------------------------------

IMAGE_BASES = {
    "flash": "gemini-3.1-flash-image",       # BELUGA / Nano Banana 2.1
    "pro": "gemini-3.0-pro-image",           # GEM_PIX_2
    "lite": "gemini-3.1-flash-lite-image",
}

IMAGE_ASPECTS = ["landscape", "portrait", "square", "four-three", "three-four"]
IMAGE_SIZES = ["2k", "4k"]

# (landscape template, portrait template); {d} = duration in seconds.
VIDEO_MODELS_T2V = {
    "fast": ("veo_3_1_t2v_fast_{d}s", "veo_3_1_t2v_fast_portrait_{d}s"),
    "standard": ("veo_3_1_t2v_{d}s", "veo_3_1_t2v_portrait_{d}s"),
    "lite": ("veo_3_1_t2v_lite_{d}s_landscape", "veo_3_1_t2v_lite_{d}s_portrait"),
    # No duration variants: these ignore --duration.
    "ultra": ("veo_3_1_t2v_fast_ultra", "veo_3_1_t2v_fast_portrait_ultra"),
    "omni": ("omni", "omni_portrait"),
}

VIDEO_MODELS_I2V = {
    "fast": ("veo_3_1_i2v_s_fast_{d}s_fl", "veo_3_1_i2v_s_fast_portrait_{d}s_fl"),
    "standard": ("veo_3_1_i2v_s_{d}s", "veo_3_1_i2v_s_portrait_{d}s"),
    "lite": ("veo_3_1_i2v_lite_{d}s_landscape", "veo_3_1_i2v_lite_{d}s_portrait"),
}

VIDEO_DURATIONS = [4, 6, 8]
VIDEO_ASPECTS = ["landscape", "portrait"]


def resolve_image_model(quality, aspect, size):
    """Compose the image model id, e.g. gemini-3.1-flash-image-landscape-2k."""
    if quality not in IMAGE_BASES:
        raise ValueError(f"unknown image quality {quality!r} (use: {', '.join(IMAGE_BASES)})")
    if aspect not in IMAGE_ASPECTS:
        raise ValueError(f"unknown aspect {aspect!r} (use: {', '.join(IMAGE_ASPECTS)})")
    if size and size not in IMAGE_SIZES:
        raise ValueError(f"unknown size {size!r} (use: {', '.join(IMAGE_SIZES)})")
    model = f"{IMAGE_BASES[quality]}-{aspect}"
    if size:
        model += f"-{size}"
    return model


def resolve_video_model(quality, duration, aspect, has_images):
    """Compose the video model id for text-to-video or image-to-video."""
    table = VIDEO_MODELS_I2V if has_images else VIDEO_MODELS_T2V
    if quality not in table:
        raise ValueError(
            f"unknown video quality {quality!r} for "
            f"{'image-to-video' if has_images else 'text-to-video'} "
            f"(use: {', '.join(table)})"
        )
    if aspect not in VIDEO_ASPECTS:
        raise ValueError(f"unknown aspect {aspect!r} (use: {', '.join(VIDEO_ASPECTS)})")
    if duration not in VIDEO_DURATIONS:
        raise ValueError(f"unknown duration {duration!r} (use: {', '.join(map(str, VIDEO_DURATIONS))})")
    template = table[quality][1 if aspect == "portrait" else 0]
    return template.format(d=duration)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def base_url():
    return os.environ.get("FLOW2API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def api_key():
    key = os.environ.get("FLOW2API_API_KEY", "").strip()
    if not key:
        print(
            "FLOW2API_API_KEY is not set.\n"
            "Add the Flow2API API key to the agent environment "
            "(Coolify env vars of the Hermes-Agent service) and retry.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return key


def auth_headers():
    return {
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
    }


def http_json(method, path, payload=None, auth=True):
    """One-shot JSON request. Returns (status, parsed_json_or_text)."""
    url = base_url() + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = auth_headers() if auth else {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"detail": body}
    except urllib.error.URLError as exc:
        raise SystemExit(f"cannot reach {url}: {exc.reason}")


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def encode_image_file(path):
    """Read a local image and return a data: URL (the API accepts data URLs)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def build_messages(prompt, image_paths=None, extend_media_id=None):
    parts = [{"type": "text", "text": prompt}]
    for path in image_paths or []:
        parts.append({"type": "image_url", "image_url": {"url": encode_image_file(path)}})
    if extend_media_id:
        # extend://MEDIA_ID continues an existing video.
        parts.append(
            {"type": "image_url", "image_url": {"url": f"extend://{extend_media_id}"}}
        )
    return [{"role": "user", "content": parts}]


def extract_media_url(content, direct_url=None):
    """Pull the media URL out of the accumulated response content."""
    if direct_url:
        return direct_url.strip()
    if not content:
        return None
    match = MARKDOWN_IMAGE_RE.search(content)
    if match:
        return match.group(1).strip()
    match = HTML_VIDEO_RE.search(content)
    if match:
        return match.group(1).strip()
    return None


def generate(model, prompt, image_paths=None, extend_media_id=None):
    """POST /v1/chat/completions with stream=true; return (media_url, raw_content)."""
    payload = {
        "model": model,
        "messages": build_messages(prompt, image_paths, extend_media_id),
        "stream": True,
    }
    req = urllib.request.Request(
        base_url() + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=auth_headers(),
        method="POST",
    )
    content_parts = []
    direct_url = None
    started = time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=READ_TIMEOUT)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        if exc.code == 401:
            raise SystemExit(
                "flow2api rejected the API key (401). "
                "Check FLOW2API_API_KEY in the agent environment."
            )
        raise SystemExit(f"flow2api HTTP {exc.code}: {body[:500]}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"cannot reach {base_url()}: {exc.reason}")

    with resp:
        for raw_line in resp:
            if time.monotonic() - started > REQUEST_TIMEOUT:
                raise SystemExit("generation timed out after 30 minutes")
            line = raw_line.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and "error" in event:
                err = event["error"]
                msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                raise SystemExit(f"flow2api error: {msg}")
            if isinstance(event, dict) and isinstance(event.get("url"), str):
                direct_url = event["url"]
            choices = event.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            message = choices[0].get("message") or {}
            text = delta.get("content") or message.get("content") or ""
            if text:
                content_parts.append(text)
            progress = delta.get("reasoning_content") or ""
            if progress:
                print(f"[flow2api] {progress.strip()}", file=sys.stderr, flush=True)

    content = "".join(content_parts)
    url = extract_media_url(content, direct_url)
    if not url:
        raise SystemExit(
            "generation finished but no media URL came back. "
            f"Raw content (truncated): {content[:500]!r}"
        )
    return url, content


def download(url, out_path):
    """Download the generated file (the /tmp cache needs no auth)."""
    req = urllib.request.Request(url, headers={"User-Agent": "flow2api-skill/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as resp:
            data = resp.read()
    except urllib.error.URLError as exc:
        raise SystemExit(f"download failed for {url}: {exc.reason}")
    with open(out_path, "wb") as fh:
        fh.write(data)
    return len(data)


def default_out(kind, url):
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm"):
        ext = ".mp4" if kind == "video" else ".png"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return os.path.abspath(f"flow2api-{kind}-{stamp}{ext}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_image(args):
    model = args.model or resolve_image_model(args.quality, args.ar, args.size)
    if args.ref and len(args.ref) > 4:
        print("warning: more than 4 reference images can destabilize generation",
              file=sys.stderr)
    url, _ = generate(model, args.prompt, image_paths=args.ref)
    out = os.path.abspath(args.out) if args.out else default_out("image", url)
    size = download(url, out)
    print(json.dumps({
        "status": "ok", "kind": "image", "model": model,
        "prompt": args.prompt, "url": url, "file": out, "bytes": size,
    }, ensure_ascii=False))


def cmd_video(args):
    has_images = bool(args.image)
    if has_images and len(args.image) > 2:
        raise SystemExit("image-to-video accepts at most 2 images (first/last frame)")
    model = args.model or resolve_video_model(
        args.quality, args.duration, args.ar, has_images
    )
    url, _ = generate(
        model, args.prompt, image_paths=args.image, extend_media_id=args.extend
    )
    out = os.path.abspath(args.out) if args.out else default_out("video", url)
    size = download(url, out)
    print(json.dumps({
        "status": "ok", "kind": "video", "model": model,
        "prompt": args.prompt, "url": url, "file": out, "bytes": size,
    }, ensure_ascii=False))


def cmd_models(args):
    status, payload = http_json("GET", "/v1/models")
    if status != 200:
        raise SystemExit(f"GET /v1/models failed ({status}): {payload}")
    rows = []
    for item in payload.get("data", []):
        model_id = item.get("id", "")
        kind = "image" if "image" in model_id else "video"
        if args.type and kind != args.type:
            continue
        rows.append({"id": model_id, "type": kind,
                     "description": item.get("description", "")})
    print(json.dumps({"status": "ok", "count": len(rows), "models": rows},
                     ensure_ascii=False, indent=2))


def cmd_health(_args):
    status, payload = http_json("GET", "/health", auth=False)
    print(json.dumps({"http_status": status, **payload}, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="flow2api.py",
        description="Generate images and videos via self-hosted Flow2API.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_img = sub.add_parser("image", help="generate an image from a text prompt")
    p_img.add_argument("--prompt", "-p", required=True, help="image prompt")
    p_img.add_argument("--model", "-m", help="full model id (overrides quality/ar/size)")
    p_img.add_argument("--quality", default="flash", choices=list(IMAGE_BASES),
                       help="flash (default, fast) | pro (max quality) | lite")
    p_img.add_argument("--ar", default="landscape", choices=IMAGE_ASPECTS,
                       help="aspect ratio (default: landscape)")
    p_img.add_argument("--size", choices=IMAGE_SIZES,
                       help="upscale tier: 2k | 4k (default: native)")
    p_img.add_argument("--ref", action="append", metavar="IMAGE",
                       help="reference image (repeatable, max 4 recommended)")
    p_img.add_argument("--out", "-o", help="output file path")
    p_img.set_defaults(func=cmd_image)

    p_vid = sub.add_parser("video", help="generate a video from a text prompt")
    p_vid.add_argument("--prompt", "-p", required=True, help="video prompt")
    p_vid.add_argument("--model", "-m", help="full model id (overrides the rest)")
    p_vid.add_argument("--quality", default="fast",
                       choices=["fast", "standard", "lite", "ultra", "omni"],
                       help="fast (default) | standard | lite | ultra | omni")
    p_vid.add_argument("--ar", default="landscape", choices=VIDEO_ASPECTS)
    p_vid.add_argument("--duration", type=int, default=8, choices=VIDEO_DURATIONS,
                       help="seconds: 4 | 6 | 8 (default: 8; ignored by ultra/omni)")
    p_vid.add_argument("--image", action="append", metavar="IMAGE",
                       help="first-frame image (2nd = last frame); switches to image-to-video")
    p_vid.add_argument("--extend", metavar="MEDIA_ID",
                       help="continue an existing video by media id")
    p_vid.add_argument("--out", "-o", help="output file path")
    p_vid.set_defaults(func=cmd_video)

    p_mod = sub.add_parser("models", help="list available generation models")
    p_mod.add_argument("--type", choices=["image", "video"], help="filter by type")
    p_mod.set_defaults(func=cmd_models)

    p_health = sub.add_parser("health", help="check the Flow2API server status")
    p_health.set_defaults(func=cmd_health)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
