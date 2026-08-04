---
name: bears-newsletter
description: Generate a Chicago Bears news newsletter via Cursor Web Search and reputable web sources. Use when the user asks for Bears news, a digest, or morning brief.
disable-model-invocation: false
---

# Bears newsletter (Cursor-only)

Generates a 2–10 minute Markdown brief by searching the web and aggregating reporting. No paid xAI or X API keys required.

## Before you write

1. Read `config/sources.json` (domains, people, broad queries, default lookback).
2. Read `scripts/prompts/newsletter_system.txt` and follow it exactly for tone, quality bar, and output sections.
3. **Prior briefs:** If `newsletters/` exists, list `*.md` there, sort by filename descending (newest first), and read up to the **5 most recent** files. Use them only for continuity — what was already reported, what may still be developing, and whether today’s window is mostly incremental vs. new news. Do not copy prior text verbatim.

## Search strategy

Use **Web Search** (multiple queries). Aim for breadth without duplicate fluff.

**Lookback:** Default `{N}` = `lookback_days_default` from config (usually 3). Honor user requests (e.g. “today only” → 1 day, “past week” → 7).

### Per-domain searches (primary first)

For each entry in `web_sources.primary`, then `local`, `national_nfl`, and `bears_community`, run a query like:

`Chicago Bears site:{domain}`

Add date context in the query when the tool supports it (e.g. “past week”, “2026”, or the current month/year).

### Broad queries

Run each string in `broad_search_queries` from config, scoped to the lookback window.

### Beat / insider names

For each person in `people.national` and `people.local_beat`, run at least one query from their `search_terms` list (these catch Schefter/Rapoport/local beat stories republished on the web).

### NFL wrap-up (closing section)

Run each string in `nfl_wrapup_queries` from config (or equivalent league-wide searches) so the newsletter can end with a short **Around the NFL** section. Prefer major national outlets (`espn.com`, `nfl.com`, `national_nfl` tiers). Keep this separate from Bears-focused reporting.

### Optional

One extra query if results are thin: `Chicago Bears site:nfl.com OR site:espn.com`.

**Do not** rely on training memory for headlines. **Do not** scrape X/Twitter directly; insider posts often appear quoted in ESPN, PFT, Yahoo, etc.

## Produce the newsletter

1. Merge and dedupe findings; prefer primary/local outlets for Bears-specific angles.
2. Write the newsletter per `newsletter_system.txt`. Set `{DATE}` to today (ISO), `{N}` to the lookback days, and estimate read time from word count.
3. Return the full Markdown to the user unchanged (formatting intact).
4. Save a copy to `newsletters/YYYY-MM-DD-HH-MM.md` when you have write access (create `newsletters/` if needed). Use 24-hour local time, zero-padded (e.g. `2026-08-04-14-30.md`) so multiple runs the same day do not overwrite each other.

## Flags / user intent

| User says | Action |
|-----------|--------|
| Today / quick hit | `--days` equivalent: 1 |
| Default digest | 3 days |
| Weekly catch-up | 7 days |
| More sources | Add domains in `config/sources.json` under the appropriate tier |

## Delegate

For an isolated run with full context, invoke the **chicago-bears-newsletter** subagent (`/chicago-bears-newsletter` or Task tool).

**Model:** That subagent is pinned to **Grok 4.5** via its agent frontmatter (`model: grok-4.5`). When launching it with the Task tool, pass `model: "cursor-grok-4.5-high"` (or omit `model` so frontmatter applies) — do not override it with another model.
