---
name: flow2api-media
description: Generate images and videos via self-hosted Flow2API. Pairs with nano-banana-prompts for prompt craft on layered composites (flyers, posters, show art).
version: 0.2.0
author: Kevinny (devkeviny), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [flow2api, image-generation, video-generation, veo, gemini]
    related_skills: [nano-banana-prompts]
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

## Writing the prompt

For a simple request, write the prompt directly in the command. For a
layered composite — an event flyer, poster, or show art with cut-out
artists, text plates, depth and a finished print look — use the
**nano-banana-prompts** skill first: it defines the prompt as pseudo-code
(`[VARIABLES]` + `[EXECUTION]`) with an explicit back-to-front layer stack,
a dimension checklist, and the proven failure modes (the white-outline
habit, layer-order drift, grain that must be asked for loudly). Then pass
the finished prompt to the script below. This skill runs generations; the
prompting skill writes them.

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

### Running from Muse (this VM)

Muse has no `FLOW2API_API_KEY` in its environment and must never ask the
user to paste the key. Run the script **inside the flow2api container** over
SSH, reading the key from the database in the same command (never print it):

```bash
# 1. Copy the script into the container (once per session is fine)
scp -o ProxyCommand="nc -X connect -x 198.19.0.1:3128 %h %p" \
  {baseDir}/scripts/flow2api.py \
  root@134.65.224.241:/tmp/flow2api.py
ssh -o ProxyCommand="nc -X connect -x 198.19.0.1:3128 %h %p" \
  root@134.65.224.241 \
  'docker cp /tmp/flow2api.py flow2api-headed-fs8og8g8ko4csows4cgko4k8:/tmp/flow2api.py'

# 2. Run it: key from admin_config.api_key, base URL localhost
#    (the generation args go on the python3 line, BEFORE the heredoc)
ssh -o ProxyCommand="nc -X connect -x 198.19.0.1:3128 %h %p" \
  root@134.65.224.241 \
  'docker exec -i flow2api-headed-fs8og8g8ko4csows4cgko4k8 python3 - image --prompt "A cat astronaut" --out /tmp/cat.png <<PYEOF
import os, sqlite3, subprocess, sys
con = sqlite3.connect("file:/app/data/flow.db?mode=ro", uri=True)
key = (con.execute("SELECT api_key FROM admin_config LIMIT 1").fetchone()[0] or "").strip()
env = dict(os.environ, FLOW2API_API_KEY=key, FLOW2API_BASE_URL="http://127.0.0.1:8000")
sys.exit(subprocess.call(["python3", "/tmp/flow2api.py"] + sys.argv[1:], env=env))
PYEOF'
```

Always `docker exec -i` when the command reads stdin. Fetch the result with
`docker cp` + `scp` and always LOOK at the image before delivering it.
Direct SSH from the Muse VM never works — the ProxyCommand via the egress
proxy is the route.

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

If the user names an exact model id (e.g. `gemini-3.1-flash-image-landscape-2k`), pass it
with `--model` — it overrides quality/ar/duration. Full catalog:
`references/models.md`.

## Critical Invariants & Pitfalls

- **NEVER substitute generation with local manual edits or mock compositions:** When the user explicitly requests image or video generation via Flow2API, do not fall back to local Photoshop/Pillow photo-manipulation or image compositing if Flow2API errors out. Doing so wastes extensive computational cycles and directly violates the user's explicit ask. Report the exact server/token error immediately so the user can resolve the underlying account/token issue.
- **Check health on Token errors:** If the script returns `没有可用的Token进行图片生成` (no active tokens available), check `flow2api.py health`. If `tokens_expired > 0` or `has_active_tokens: false`, the Google session cookies in Flow2API expired (HTTP 401). Immediately notify the user to re-sync Google cookies in the Flow2API panel (`https://flow2api.kevinny.tech`), then stop.
- **captcha_method must be `browser` for generation:** `personal` fails — Google redirects the container browser to the sign-in page and the reCAPTCHA token comes back empty (proven 24/nov). A raw SQL change of captcha_method does NOT take effect until a container restart (or the panel API, which hot-reloads). Never change it without the user's order.
- **A generation takes ~75–130s.** Do not treat a slow call as hung.

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
