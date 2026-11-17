# hermes-flow2api-skill

Hermes Agent skill that generates **images and videos** through a self-hosted
[Flow2API](https://github.com/TheSmallHanCat/flow2api) server — Google Flow
(Veo video, Gemini image models) exposed as an OpenAI-compatible API, paid
with the Google account's own Flow credits.

## What's inside

```
flow2api-media/
  SKILL.md                  # the skill (frontmatter + instructions)
  scripts/flow2api.py       # stdlib-only Python CLI (no pip packages)
  references/models.md      # full model catalog
```

## Install in Hermes Agent

Copy the skill directory into the user skills folder (the whole directory —
the script lives next to `SKILL.md`):

```bash
git clone https://github.com/devkeviny/hermes-flow2api-skill.git
cp -r hermes-flow2api-skill/flow2api-media ~/.hermes/skills/
hermes skills list | grep flow2api
```

No gateway restart needed — new sessions pick the skill up. Do not add it to
`skills.auto_load`; it loads on demand when the user asks for media.

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

Or call the script directly:

```bash
python3 flow2api-media/scripts/flow2api.py image --prompt "A cat astronaut" --out cat.png
python3 flow2api-media/scripts/flow2api.py video --prompt "Waves crashing" --ar portrait --duration 4 --out waves.mp4
python3 flow2api-media/scripts/flow2api.py models --type video
python3 flow2api-media/scripts/flow2api.py health
```

See `flow2api-media/SKILL.md` for the full usage guide and
`flow2api-media/references/models.md` for the model catalog.

## Security

No secrets live in this repo. The API key is only ever read from the
environment at runtime, never printed, logged, or stored by the skill.
