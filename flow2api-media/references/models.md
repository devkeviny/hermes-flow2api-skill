# Flow2API Model Catalog

Model ids from `MODEL_CONFIG` in upstream flow2api (`src/services/generation_handler.py`)
plus the alias resolver (`src/core/model_resolver.py`). The script composes these
ids from `--quality` / `--ar` / `--size` / `--duration`; `--model` accepts any id
below verbatim.

## What is "Nano Banana"?

"Nano Banana" is Google's nickname for its Gemini image generation and
editing family (official product name: Gemini Image). It is not one model —
there are five, and the skill exposes three of them:

| Nickname | Official name | Released | Character |
|---|---|---|---|
| Nano Banana | Gemini 2.5 Flash Image | Aug 2025 | The original; legacy now |
| Nano Banana Pro | Gemini 3 Pro Image | Nov 2025 | Slowest, most precise, best text inside images; up to 4K |
| Nano Banana 2 | Gemini 3.1 Flash Image | Feb 2026 | The fast workhorse; being replaced by 2.1 |
| Nano Banana 2 Lite | Gemini 3.1 Flash-Lite Image | Jun 2026 | Fastest and cheapest |
| Nano Banana 2.1 | Gemini Nano Banana 2.1 | Oct 2026 | The newest; Google's best everyday image model |

There is no version literally called "Nano Banana 2.0" — the 2.x line is
Nano Banana 2, 2 Lite and 2.1. Pro is a separate branch (precision), not a
newer version of 2.

### How the skill's flags map to them

| Flag | Flow2API model id | Engine | Nano Banana |
|---|---|---|---|
| `--quality flash` (default) | `gemini-3.1-flash-image` | BELUGA | Nano Banana 2.1 |
| `--quality pro` | `gemini-3.0-pro-image` | GEM_PIX_2 | Nano Banana Pro |
| `--quality lite` | `gemini-3.1-flash-lite-image` | — | Nano Banana 2 Lite |

## Images

Full id: `{base}-{aspect}` with optional `-2k` / `-4k` upscale suffix.

| Aspect flag | Suffix | Ratio |
|---|---|---|
| `landscape` (default) | `-landscape` | 16:9 |
| `portrait` | `-portrait` | 9:16 |
| `square` | `-square` | 1:1 |
| `four-three` | `-four-three` | 4:3 |
| `three-four` | `-three-four` | 3:4 |

Examples: `gemini-3.1-flash-image-landscape`,
`gemini-3.0-pro-image-portrait-2k`, `gemini-3.1-flash-image-square-4k`.

Reference images (image-to-image / edit) work with any image model: pass
`--ref` one or more times. Keep it to 2–4 references.

## Videos — text-to-video (T2V)

| Quality flag | Landscape id | Portrait id |
|---|---|---|
| `fast` (default) | `veo_3_1_t2v_fast_{4,6,8}s` | `veo_3_1_t2v_fast_portrait_{4,6,8}s` |
| `standard` | `veo_3_1_t2v_{4,6,8}s` | `veo_3_1_t2v_portrait_{4,6,8}s` |
| `lite` | `veo_3_1_t2v_lite_{4,6,8}s_landscape` | `veo_3_1_t2v_lite_{4,6,8}s_portrait` |
| `ultra` | `veo_3_1_t2v_fast_ultra` | `veo_3_1_t2v_fast_portrait_ultra` |
| `omni` | `omni` | `omni_portrait` |

`ultra` and `omni` have no duration variants — `--duration` is ignored for
them. `omni` is Omni 1.2 Flash (also reachable via the alias
`omni-1.2-flash-8s-landscape`).

4K / 1080p quality variants also exist upstream (e.g.
`veo_3_1_t2v_8s_4k`, `veo_3_1_t2v_8s_1080p`); pass them with `--model`.

## Videos — image-to-video (I2V)

Used automatically when `--image` is passed (1 image = first frame,
2 images = first + last frame).

| Quality flag | Landscape id | Portrait id |
|---|---|---|
| `fast` (default) | `veo_3_1_i2v_s_fast_{4,6,8}s_fl` | `veo_3_1_i2v_s_fast_portrait_{4,6,8}s_fl` |
| `standard` | `veo_3_1_i2v_s_{4,6,8}s` | `veo_3_1_i2v_s_portrait_{4,6,8}s` |
| `lite` | `veo_3_1_i2v_lite_{4,6,8}s_landscape` | `veo_3_1_i2v_lite_{4,6,8}s_portrait` |

## Video continuation

`--extend <MEDIA_ID>` continues an existing video (`extend://` upstream).
The media id comes from a previous generation's Flow project.

## Notes

- Credit cost varies by model, duration, and resolution, and is charged
  against the connected Google account's Flow credits. Check the balance in
  the Flow web UI — the number the flow2api panel shows comes from a legacy
  endpoint and can differ from the UI.
- Some models require a paid tier (Pro/Ultra) on the Google account.
  If generation fails with a tier error, the account needs the upgrade —
  the skill cannot work around it.
- `flow2api.py models` lists the live catalog from the server; prefer it
  over this file when they disagree.
