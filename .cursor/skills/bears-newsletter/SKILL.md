---
name: bears-newsletter
description: Generate a Chicago Bears news newsletter using Grok 4.5 X Search and reputable sources. Use when the user asks for Bears news, a digest, or morning brief.
disable-model-invocation: false
---

# Bears newsletter

Generates a 2–10 minute Markdown brief from X and web sources via xAI.

## Steps

1. Ensure `XAI_API_KEY` is set (see `.env.example`).
2. Install deps and run from repo root:

```bash
pip install -r requirements.txt
python3 scripts/generate_bears_newsletter.py --days 3
```

3. Return the script output to the user unchanged (formatting intact).

## Flags

| Flag | Purpose |
|------|---------|
| `--days N` | Lookback window (default 3) |
| `--stdout-only` | Skip writing `newsletters/` |
| `--model grok-4.5` | Override model |

## Customize sources

Edit `config/sources.json` — X handles (max 20 combined) and web domains for Athletic/ESPN coverage.

## Delegate

For a isolated run with full context, invoke the **chicago-bears-newsletter** subagent (`/chicago-bears-newsletter` or Task tool).
