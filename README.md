# hermes-flow2api-skill

Two skills for generating images and videos with Google's Nano Banana
family through a self-hosted [Flow2API](https://github.com/TheSmallHanCat/flow2api)
server — Google Flow (Veo video, Gemini image models) exposed as an
OpenAI-compatible API, paid with the Google account's own Flow credits.

- **`flow2api-media`** (v0.2.0) — the execution skill: runs image and video
  generation through Flow2API via a stdlib-only Python CLI.
- **`nano-banana-prompts`** (v1.0.0) — the prompting skill: writes prompts
  that hold up — pseudo-code structure, dimension checklist, anti-patterns,
  and a proven recipe for event flyers / show posters with layered
  composites, cut-out artists and a finished print look.

One writes the prompt, the other runs it. Both are installed in Hermes
Agent and in Muse.

## What's inside

```
flow2api-media/
  SKILL.md                  # the skill (frontmatter + instructions)
  scripts/flow2api.py       # stdlib-only Python CLI (no pip packages)
  references/models.md      # full model catalog
nano-banana-prompts/
  SKILL.md                  # the prompting skill
```

## Install in Hermes Agent

Copy the skill directories into the user skills folder (whole directories —
the script lives next to `SKILL.md`):

```bash
git clone https://github.com/devkeviny/hermes-flow2api-skill.git
cp -r hermes-flow2api-skill/flow2api-media hermes-flow2api-skill/nano-banana-prompts ~/.hermes/skills/
hermes skills list | grep -E 'flow2api-media|nano-banana-prompts'
```

No gateway restart needed — new sessions pick the skills up. Do not add
them to `skills.auto_load`; they load on demand when the user asks for
media.

## Install in Muse

Same files, into the Muse custom skills folder:

```bash
cp -r flow2api-media nano-banana-prompts ~/workspace/custom-skills/
```

In Muse, `flow2api-media` runs the script **inside the flow2api container**
over SSH (the API key is read from the database in the same command — see
"Running from Muse" in `flow2api-media/SKILL.md`). Never paste the key into
chat.

## Configure

The script reads its credentials **only from the environment**:

| Variable | Required | Meaning |
|---|---|---|
| `FLOW2API_API_KEY` | yes | API key from the Flow2API panel |
| `FLOW2API_BASE_URL` | no | Server base URL (default `https://flow2api.kevinny.tech`) |

On a Coolify-managed Hermes install, add `FLOW2API_API_KEY` to the
Hermes-Agent service env vars. Never commit the key — this repo is public.

## Use

Ask the agent in plain language:

- "gera uma imagem de um gato astronauta"
- "cria um vídeo de 8 segundos de ondas quebrando nas pedras, vertical"
- "anima essa imagem"
- "cria um flyer de show com 3 cantores" (uses `nano-banana-prompts` to
  write the prompt, `flow2api-media` to run it)

Or call the script directly:

```bash
python3 flow2api-media/scripts/flow2api.py image --prompt "A cat astronaut" --out cat.png
python3 flow2api-media/scripts/flow2api.py video --prompt "Waves crashing" --ar portrait --duration 4 --out waves.mp4
python3 flow2api-media/scripts/flow2api.py models --type video
python3 flow2api-media/scripts/flow2api.py health
```

See `flow2api-media/SKILL.md` for the full usage guide,
`flow2api-media/references/models.md` for the model catalog, and
`nano-banana-prompts/SKILL.md` for prompt craft.

## Security

No secrets live in this repo. The API key is only ever read from the
environment at runtime, never printed, logged, or stored by the skill.
