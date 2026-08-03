#!/usr/bin/env python3
"""Generate a Chicago Bears news newsletter via xAI Grok 4.5 + X Search + Web Search."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "sources.json"
PROMPT_PATH = ROOT / "scripts" / "prompts" / "newsletter_system.txt"
NEWSLETTERS_DIR = ROOT / "newsletters"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def all_x_handles(config: dict) -> list[str]:
    handles: list[str] = []
    for group in config["x_handles"].values():
        for entry in group:
            handles.append(entry["handle"])
    # API max is 20; dedupe while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for h in handles:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    return unique[:20]


def build_user_prompt(*, days: int, handles: list[str], domains: list[str]) -> str:
    today = date.today().isoformat()
    handle_list = ", ".join(f"@{h}" for h in handles)
    domain_list = ", ".join(domains)
    return f"""Today is {today}. Build today's Chicago Bears newsletter.

Search window: the past {days} calendar days (inclusive through today).

Use x_search to gather posts from these handles only: {handle_list}.
Also search X broadly for Chicago Bears news, but weight the allowlisted handles above.

Use web_search focused on these domains when possible: {domain_list}.
Find recent Bears stories from The Athletic and ESPN especially.

After searching, write the newsletter following the system format. Replace {{DATE}} with {today} and set {{N}} to {days}. Estimate read time honestly from word count.

Return ONLY the final newsletter Markdown — no preamble about your search process."""


def extract_output_text(response) -> str:
    """Pull assistant text from an xAI / OpenAI Responses API object."""
    parts: list[str] = []

    output = getattr(response, "output", None)
    if output:
        for item in output:
            item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
            if item_type == "message":
                content = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else None)
                if not content:
                    continue
                for block in content:
                    btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
                    if btype in ("output_text", "text"):
                        text = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
                        if text:
                            parts.append(text)

    if parts:
        return "\n".join(parts).strip()

    # Fallbacks for SDK variations
    if hasattr(response, "output_text") and response.output_text:
        return str(response.output_text).strip()

    return str(response).strip()


def generate_newsletter(*, days: int, model: str | None = None) -> str:
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "XAI_API_KEY is not set. Get a key at https://console.x.ai/ and export it, "
            "or add it as a secret in Cursor Cloud Agents."
        )

    config = load_config()
    handles = all_x_handles(config)
    domains = config.get("web_domains", [])
    model_id = model or config.get("model", "grok-4.5")

    from_date = (datetime.now(timezone.utc).date() - timedelta(days=days - 1)).isoformat()
    to_date = datetime.now(timezone.utc).date().isoformat()

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = build_user_prompt(days=days, handles=handles, domains=domains)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Install dependencies: pip install -r requirements.txt") from exc

    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    tools = [
        {
            "type": "x_search",
            "allowed_x_handles": handles,
            "from_date": from_date,
            "to_date": to_date,
        },
        {
            "type": "web_search",
            "filters": {"allowed_domains": domains[:5]},
        },
    ]

    response = client.responses.create(
        model=model_id,
        instructions=system_prompt,
        input=[{"role": "user", "content": user_prompt}],
        tools=tools,
    )

    return extract_output_text(response)


def save_newsletter(content: str, *, out_path: Path | None = None) -> Path:
    NEWSLETTERS_DIR.mkdir(parents=True, exist_ok=True)
    path = out_path or NEWSLETTERS_DIR / f"{date.today().isoformat()}.md"
    path.write_text(content + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Chicago Bears newsletter via Grok + X Search")
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="How many calendar days back to include (default: 3)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="xAI model id (default: from config, grok-4.5)",
    )
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="Print to stdout only; do not write newsletters/ file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output file path",
    )
    args = parser.parse_args()

    if args.days < 1 or args.days > 14:
        parser.error("--days must be between 1 and 14")

    print("Fetching Bears news with Grok (X Search + Web Search)...", file=sys.stderr)
    content = generate_newsletter(days=args.days, model=args.model)

    if not content:
        raise SystemExit("Empty response from xAI API")

    if args.stdout_only and not args.output:
        print(content)
        return

    path = save_newsletter(content, out_path=args.output)
    print(content)
    print(f"\nSaved to {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
