"""Command-line front end.

    pm-os refresh                       download N-PORT holdings + Treasury curve, print a summary
    pm-os status                        show cached data, as-of dates and sources
    pm-os ask "what if rates rise 100bp?"
    pm-os chat                          interactive session (follow-ups keep context)
    pm-os tool run_scenario '{"type": "parallel", "params": {"bp": 100}}'   call one tool, no LLM

Add --cheap to use the cheaper model, --no-web to skip web search.
"""

from __future__ import annotations

import argparse
import json
import sys

from agent import tools


def _print_json(obj):
    print(json.dumps(obj, indent=2, default=str))


def cmd_refresh(_args):
    report = tools.refresh_data()
    _print_json(report)
    try:
        _print_json(tools.fetch_holdings())
        _print_json(tools.get_portfolio(view="sma", max_rows=5)["summary"])
    except Exception as exc:
        print(f"\nNo holdings available: {exc}", file=sys.stderr)


def cmd_status(_args):
    for m in tools.data_status()["cache"]:
        print(f"{m['name']:<32} as of {m['as_of']}  fetched {m['fetched_at']}\n    {m['source_url']}")


def cmd_tool(args):
    _print_json(tools.dispatch(args.name, json.loads(args.json_args or "{}")))


def _render(result):
    print("\n" + result.answer)
    print("\n--- audit trail ---")
    for step in result.audit_trail:
        out = step["output"]
        flag = "ERROR " if "error" in out else ""
        print(f"  {flag}{step['tool']}({json.dumps(step['input'])})  as_of={out.get('as_of')}")
    for q in result.web_searches:
        print(f"  web_search: {q}")
    for s in result.sources:
        if s["cited"]:
            print(f"  source: {s['title']} - {s['url']}")


def _agent(args):
    from agent.loop import MODELS, PMAgent
    return PMAgent(model=MODELS["cheap"] if args.cheap else None, web_search=not args.no_web)


def cmd_ask(args):
    agent = _agent(args)
    _render(agent.ask(" ".join(args.question),
                      on_step=lambda e: print(f"  ... {e.get('tool') or 'web_search'}", file=sys.stderr)))


def cmd_chat(args):
    agent = _agent(args)
    print("PM-OS chat. Ask about the portfolio; 'quit' to exit.")
    while True:
        try:
            q = input("\nPM> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("quit", "exit", ""):
            break
        _render(agent.ask(q, on_step=lambda e: print(f"  ... {e.get('tool') or 'web_search'}", file=sys.stderr)))


def main(argv=None):
    p = argparse.ArgumentParser(prog="pm-os", description="Fixed income SMA analyst on real public data.")
    p.add_argument("--cheap", action="store_true", help="use the cheaper model")
    p.add_argument("--no-web", action="store_true", help="disable web search")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("refresh").set_defaults(fn=cmd_refresh)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    a = sub.add_parser("ask")
    a.add_argument("question", nargs="+")
    a.set_defaults(fn=cmd_ask)
    sub.add_parser("chat").set_defaults(fn=cmd_chat)
    t = sub.add_parser("tool")
    t.add_argument("name", choices=sorted(tools.TOOL_FUNCTIONS))
    t.add_argument("json_args", nargs="?")
    t.set_defaults(fn=cmd_tool)
    args = p.parse_args(argv)
    try:
        args.fn(args)
    except RuntimeError as exc:          # e.g. missing API key: say so plainly, no traceback
        sys.exit(f"pm-os: {exc}")


if __name__ == "__main__":
    main()
