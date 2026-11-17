---
name: flow2api-media
description: Generate images and videos via self-hosted Flow2API.
version: 0.1.0
author: Kevinny (devkeviny), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [flow2api, image-generation, video-generation, veo, gemini]
    related_skills: []
---

# Flow2API Media Generation

Generate images and videos through the user's self-hosted Flow2API server
(`https://flow2api.kevinny.tech`), which exposes Google Flow — Veo video and
Gemini image models — as an OpenAI-compatible API, paid with the Google
account's own Flow credits.

## When to Use

- The user asks to generate, create, or draw an image or video.
- The user wants to animate an image, continue a video, or vary an existing
  image with a reference.
- Do NOT use for: text chat, image analysis, or editing files — this skill
  only generates media.

## Setup (one time)

The script reads its credentials **only from the environment**. Never put the
API key in a file, a prompt, or a message.

| Variable | Required | Meaning |
|---|---|---|
| `FLOW2API_API_KEY` | yes | API key from the Flow2API panel (Settings / API Keys) |
| `FLOW2API_BASE_URL` | no | Server base URL (default `https://flow2api.kevinny.tech`) |

On the Hermes host the key lives in the Hermes-Agent service env vars
(Coolify). If a call fails with `FLOW2API_API_KEY is not set` or a 401, tell
the user the key is missing/wrong and stop — do not invent a key.

## Script

`{baseDir}` = this SKILL.md's directory. The only runtime is stdlib Python 3
(no pip packages):

```bash
python3 {baseDir}/scripts/flow2api.py <command> [options]
```

Every successful generation prints one JSON line on stdout with `status`,
`kind`, `model`, `prompt`, `url` (remote file), `file` (local path) and
`bytes`. Progress notes go to stderr. Exit codes: 0 ok, 1 API/generation
error, 2 usage/config error.

## Usage

```bash
# Image — fast default (Nano Banana 2.1), landscape
python3 {baseDir}/scripts/flow2api.py image --prompt "A cat astronaut" --out cat.png

# Image — max quality, portrait, 2K upscale
python3 {baseDir}/scripts/flow2api.py image --prompt "A lighthouse at dusk" \
  --quality pro --ar portrait --size 2k --out lighthouse.png

# Image from a reference (keeps the subject, changes the scene)
python3 {baseDir}/scripts/flow2api.py image --prompt "Same person, beach at sunset" \
  --ref person.png --out beach.png

# Video — 8s fast default, landscape
python3 {baseDir}/scripts/flow2api.py video --prompt "Waves crashing on rocks" --out waves.mp4

# Video — vertical, 4s, standard quality
python3 {baseDir}/scripts/flow2api.py video --prompt "A dancer spinning" \
  --ar portrait --duration 4 --quality standard --out dance.mp4

# Video from an image (first frame; a 2nd --image is the last frame)
python3 {baseDir}/scripts/flow2api.py video --prompt "The lighthouse beam sweeps" \
  --image lighthouse.png --out beam.mp4

# Continue an existing video by media id
python3 {baseDir}/scripts/flow2api.py video --prompt "The camera pulls back" \
  --extend <MEDIA_ID> --out part2.mp4

# List models / check the server
python3 {baseDir}/scripts/flow2api.py models --type video
python3 {baseDir}/scripts/flow2api.py health
```

## Picking Parameters From Natural Language

The user describes what they want; the agent picks the flags. Defaults when
the user doesn't say otherwise:

| User says | Flags |
|---|---|
| just "an image" / "a picture" | `image`, defaults (flash, landscape) |
| "high quality" / "best quality" image | `--quality pro` |
| "vertical" / "stories" / "reels" / "9:16" | `--ar portrait` |
| "square" / "profile picture" | `--ar square` |
| "2K" / "4K" / "upscale" | `--size 2k` / `--size 4k` |
| "a video" | `video`, defaults (fast, 8s, landscape) |
| "short video" / "4 seconds" | `--duration 4` |
| "best quality video" | `--quality standard` (slower, better) |
| "cheapest/quickest video" | `--quality lite` |
| "animate this image" | `video --image <file>` |
| "continue this video" | `video --extend <MEDIA_ID>` |

If the user names an exact model id (e.g. `veo_3_1_t2v_fast_8s`), pass it
with `--model` — it overrides quality/ar/duration. Full catalog:
`references/models.md`.

## After Generation

1. Confirm the local file exists and is non-empty before reporting success.
2. Tell the user the model used, the local path, and the remote URL.
3. If the channel supports it, attach/send the generated file itself — the
   user asked for media, not for a path.
4. Generation consumes the Google account's Flow credits. If the API reports
   quota exhaustion (429 / "quota"), say so plainly and stop — do not retry
   in a loop.

## Errors

| Symptom | Meaning / action |
|---|---|
| `FLOW2API_API_KEY is not set` | Key missing from the environment — user must add it (Coolify env) |
| 401 | Key wrong or revoked — user must rotate it in the Flow2API panel |
| 429 | Quota exhausted or rate-limited — wait, do not hammer retries |
| `no media URL came back` | Upstream generation failed — retry once; if it persists, report it |
| Timeout after 30 min | Generation stalled server-side — check `health`, report it |

## Security

- The API key is a secret: never print it, never paste it into a file,
  message, or log, and never commit it. The repo this skill ships in is
  public.
- Generated files may contain anything the user prompted — treat them as
  the user's own media.
