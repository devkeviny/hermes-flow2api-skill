---
name: nano-banana-prompts
description: Use when writing a prompt to generate or edit an image with a Nano Banana family model (gemini-3.1-flash-image / gemini-3.0-pro-image via flow2api) — especially layered composites like event flyers, posters and show art, where layer order, text, depth and a finished print look matter. This skill writes prompts; flow2api-media runs them.
version: 1.0.0
author: Kevinny (devkeviny)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [nano-banana, image-generation, prompting, gemini, flyer, poster]
    related_skills: [flow2api-media]
---

# Nano Banana Prompts

Write prompts for Google's Nano Banana image family (Gemini Image) as
served by the user's self-hosted Flow2API. Execution lives in the
**flow2api-media** skill — this skill only writes the prompt.

## Core principle

Nano Banana reasons over structure. A flat paragraph lets the model
improvise the composition; a **pseudo-code prompt** — `[VARIABLES]` with
one named asset per element, then an `[EXECUTION]` block that states the
order and the rules — holds it together. Define lighting and camera as
variables too: the model uses focal length, aperture and light direction to
compute depth of field and shadows.

## Prompt structure

```
[VARIABLES]
SUBJECT = "..."        # specific, with materials and texture
SETTING = "..."        # where, with atmosphere
STYLE = "..."          # photorealistic / illustration / 3D render / ...
LIGHTING = "..."       # ONE key light, angle + elevation
CAMERA = "..."         # body + lens + aperture, e.g. Canon EOS R5, 85mm, f/2.8
MOOD = "..."           # the feeling
TEXT = "..."           # exact text, quoted (omit when the image has no text)
FINISH = "..."         # grain + grade, applied over everything

[EXECUTION]
Compose ... (state the order and the spatial relations explicitly).
Light every element with LIGHTING and render the photographic parts with CAMERA.
Render all text exactly as written, with correct spelling.
```

Not every variable is needed every time — use what the asset needs, keep
one coherent creative direction.

## Dimension checklist

When a request is vague, pin these down (ask, or infer from the use case):
subject, setting, mood, style, composition, lighting, purpose (where the
asset ships — the model infers lighting/composition/mood from it), exact
text, format (aspect ratio + resolution). Mood and lighting move quality
the most — never leave both unspecified.

## Text

Quote every piece of in-image text exactly, in Portuguese, inside the
variable that owns it. Short text renders best; keep each line under ~25
characters. End the prompt with "Render all text exactly as written, with
correct spelling." If the image must have NO text, say "no text, no
typography, no watermarks, no labels" — the model otherwise invents
captions.

## Editing, don't re-roll

When a result is mostly right, send the image back with a precise change
instruction instead of generating fresh. The model preserves what you
don't mention. Editing is this family’s strength: it is cheaper, keeps
what's already right, and keeps the same faces — a fresh generation
re-rolls every face. State the change and what must stay identical.

## Anti-patterns

- Tag soup (disconnected keywords) — rewrite as sentences / variables.
- Vague subjects ("a person", "a building") — add specifics and materials.
- Missing mood/lighting.
- No purpose context.
- Over-prompting — contradictory or excessive detail confuses composition;
  one coherent creative direction per prompt.
- Re-rolling instead of editing (see above).

## Recipe: event flyer / show poster (proven, 3 rounds, 24/nov)

The flagship composite. One variable per layer, composited in this exact
back-to-front order:

1. Background colour/pattern
2. City/landscape photo, cut along rooflines, top edge just below the
   artists' head height, with a soft drop shadow under the cut edge
3. Background truss (photorealistic 3D, Cinema 4D quality, bolts and
   cross-bracing visible) with spotlights
4. Colour plate behind the artists (e.g. small blue corrugated container
   panel, weathered steel, scratches, rust spots) — keep it SMALL, about
   two thirds of the width and one third of the height
5. Artists (photographic cut-outs, realistic skin texture)
6. Title
7. Black-to-transparent gradient, bottom to top, in front of the artists'
   lower bodies and the city, behind the text
8. Name plates, city pill, corner info, footer
9. Foreground truss duplicated in the extreme foreground, bottom corners
   only, heavily blurred and darkened, never covering text
10. Finish: grain + grade over everything

### His design vocabulary (translate before prompting)

| He says | Prompt language |
|---|---|
| fubento (cores apagadas, pouco contraste) | matte faded film look: lifted blacks (darkest tones dark grey, never pure black), reduced contrast, slightly desaturated muted colours, soft faded highlights |
| granulação / ruído | clearly visible fine 35mm film grain over the whole image, like Kodak Portra grain |
| sombra dura branca, não contorno | flat hard-edged solid white drop shadow projected diagonally behind the cut-out, offset up and to the left ONLY; white visible ONLY on the upper-left side; right and bottom edges have NO white at all; NO outline, NO stroke, NO border |
| treliça na frente, desfocada, nos cantos | same truss duplicated in the extreme foreground, bottom corners only, heavily blurred out of focus and darkened, framing the composition |
| feno (festa junina / roça) | blurred hay bales on both sides in the foreground, one in the middle as a support for the elements |
| luz dos artistas igual à do flyer | one single consistent key light, upper center-front at 45° elevation, matching the stage spotlights; soft shadows falling consistently down and to the right |
| realista (placa, treliça, cidade) | photorealistic + material detail: weathered steel with scratches and rust, aluminium truss with bolts/clamps, real photograph textures, skin with pores |

### Compact worked example (flyer, 3 fictional singers)

```
[VARIABLES]
BACKGROUND = "Deep red diamond-mesh pattern, dark, subtle"
CITY = "Black-and-white favela skyline photograph, cut along the rooflines, top edge just below the artists' head height, soft drop shadow under the cut edge"
TRUSS_BACK = "Photorealistic aluminium stage truss towers, Cinema 4D quality, bolts and cross-bracing visible, with spotlights aimed at the artists"
PLATE = "Small blue corrugated container panel, weathered steel with scratches and rust spots, two thirds of the width, one third of the height, behind the artists"
SINGER_1 = "Photographic cut-out of a fictional male forró singer in a black shirt, realistic skin texture"
SINGER_2 = "Photographic cut-out of a fictional male forró singer in a white shirt, realistic skin texture"
SINGER_3 = "Photographic cut-out of a fictional male forró singer in a denim jacket, realistic skin texture"
SHADOW = "Flat hard-edged solid white drop shadow projected diagonally behind each cut-out, offset up and to the left ONLY; white visible ONLY on the upper-left side; right and bottom edges have NO white at all; NO outline, NO stroke, NO border"
LIGHTING = "One single key light, upper center-front at 45° elevation, matching the stage spotlights"
CAMERA = "Canon EOS R5, 85mm portrait lens, f/2.8"
TITLE = "Forró Prime"
NAMES = "CAIO FERNANDES, BRUNO ALMEIDA, FELIPE CASTRO"
FINISH = "Matte faded film look: lifted blacks, reduced contrast, slightly desaturated muted colours; clearly visible fine 35mm film grain over the whole image"

[EXECUTION]
Composite back to front: BACKGROUND, CITY, TRUSS_BACK, PLATE, the three singers with SHADOW, TITLE, a black-to-transparent gradient bottom to top in front of the singers' lower bodies, NAMES on alternating black/white/black plates, then the same truss duplicated in the extreme foreground, bottom corners only, heavily blurred and darkened, never covering text. Finish with FINISH over everything. Render all text exactly as written, with correct spelling.
```

Never reproduce real celebrities from a reference image — use fictional
artists; the user supplies real names/details when he wants a final
version.

## Proven failure modes (three real rounds, 24/nov)

- **White outline habit (strongest):** the model defaults to a full white
  sticker outline around cut-outs even when told "NO outline, offset shadow
  only". Three increasingly explicit attempts (v1, v2, v3) all came back
  with an outline on at least two of three singers. Fix by image-to-image
  edit on the finished poster, asking only to convert the outline into an
  offset shadow — editing is this model family's strength, and a single
  targeted edit beats re-rolling the whole poster.
- **Layer order drifts in prose:** in v2 the city landed at the bottom
  instead of behind the singers. The `[VARIABLES]` + `[EXECUTION]` order
  fixed it in v3.
- **Grain must be asked for LOUDLY:** "fine film grain" in v1/v2 was
  invisible; "clearly visible fine 35mm film grain" plus the faded grade
  showed in v3.
- **Faces re-roll every generation:** each text-to-image run invents new
  faces. To keep the same artists across versions, edit the previous image
  instead of generating fresh.

## Generation facts (flow2api)

- Model: `gemini-3.1-flash-image` serves the Nano Banana 2.1 engine in
  Flow; `gemini-3.0-pro-image` is Nano Banana Pro. There is NO model
  literally named "nano-banana" in this catalog and NO
  `/v1/images/generations` route — image calls go through
  `POST /v1beta/models/{model}:generateContent` (see flow2api-media).
- Aspects: landscape, portrait, square, four-three, three-four, each also
  in `-2k`/`-4k`. A 3:4 portrait poster at 2K renders 1792x2400.
- A generation takes ~75–130s. Always LOOK at the image before delivering
  it.
- captcha_method must be `browser` for generation: `personal` fails
  (Google redirects the container browser to sign-in; reCAPTCHA token
  comes back empty). A raw SQL change does NOT take effect until a
  container restart.

## Public Nano Banana skills surveyed (24/nov — don't redo this)

Most public "nano-banana skills" are thin execution wrappers (a SKILL.md
telling the agent to run a script/CLI/MCP), not prompting craft, and ALL of
them assume a paid Gemini API key (image models have zero free-tier API
quota), Gemini CLI, MCP, or a third-party platform — none fits flow2api, so
installing one buys nothing. Harvest the prompting half only:

- **kryptobaseddev/awesome-skills `image-nanobanana`** (v1.2.0, MIT) — the
  most complete skill: preflight + direct-API generator + gemini-cli path +
  production workflow + per-asset recipes + a real prompting guide
  (`references/prompting.md`: dimension checklist, technique library, text
  rendering, anti-patterns, calibration examples). Source of the checklist
  and anti-patterns above.
  https://github.com/kryptobaseddev/awesome-skills/tree/main/skills/image-nanobanana
- **shinpr/mcp-image** (100 stars, survey score 9/10) — best code quality;
  novel two-stage prompt optimization (Gemini 2.5 Flash rewrites the prompt
  with a Subject-Context-Style framework before generation). Its SKILL.md
  is model-agnostic and teaches prompting. Quality preset broken (dead pro
  model). https://github.com/shinpr/mcp-image
- **kingbootoshi/nano-banana-2-skill** (347 stars, survey 7/10) —
  most-starred dedicated skill; Bun/TS CLI with image-to-image,
  transparent-background pipeline (green screen + FFmpeg colorkey/despill),
  cost tracking. A tool, not a prompting guide; pro alias points to a dead
  model. https://github.com/kingbootoshi/nano-banana-2-skill
- **ckorhonen/claude-skills `nano-banana`** — MCP-based; "Precision Mode"
  with structured JSON prompt schemas (marketing_image, ui_builder,
  diagram_spec). Worth borrowing when exact reproducibility matters.
- **Survey:** MohamedAbdallah-14/prompt-to-asset,
  `docs/research/34-installable-skills-survey/nano-banana-skills.md` (Apr
  2026) — scored comparison of the installable skills; several repos are
  non-functional because `gemini-3-pro-image-preview` shut down 2026-03-09.
  Star count does not mean working.
