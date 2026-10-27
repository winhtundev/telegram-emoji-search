#!/usr/bin/env python3
"""
Telegram Emoji Search - MCP server (stdlib only, no pip packages needed).

Exposes the 2,412 emojis from emojis.json as MCP tools over stdio,
so an MCP client (Muse, Claude Desktop, etc.) can search them.

Tools:
  - search_emojis(query, pack=None, limit=20)
      Search by name / pack / id (multi-word AND, like the website).
      Returns name, pack, id, and direct GitHub Pages links for
      the animated WebM and the static thumbnail.
  - get_emoji(id)
      Full record for one custom-emoji id.
  - list_packs()
      All packs with their emoji counts.

Data source:
  By default emojis.json sitting next to this file. Override with
  the EMOJI_JSON environment variable, or pass the path as argv[1].

Base URL for links (override with EMOJI_BASE_URL):
  https://winhtundev.github.io/telegram-emoji-search/
  Links are built as <base>/webm/<pack>/<id>.webm and
  <base>/thumbs/<pack>/<id>.jpg, matching the site layout.

Protocol: MCP over stdio, JSON-RPC 2.0, newline-delimited messages.
Run:  python3 mcp_server.py
Then point your MCP client at that command (see MCP_README.md).
"""

import json
import os
import sys

BASE_URL = os.environ.get(
    "EMOJI_BASE_URL", "https://winhtundev.github.io/telegram-emoji-search/"
).rstrip("/") + "/"


def load_data():
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EMOJI_JSON")
    if not path:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emojis.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


DATA = load_data()
BY_ID = {str(e["id"]): e for e in DATA}


def public_record(e):
    rec = {
        "id": str(e["id"]),
        "name": e.get("name"),
        "pack": e.get("pack"),
        "alt": e.get("alt"),
    }
    if e.get("webm"):
        rec["webm_url"] = BASE_URL + e["webm"]
    if e.get("thumb"):
        rec["thumb_url"] = BASE_URL + e["thumb"]
    return rec


def tool_search_emojis(args):
    query = (args.get("query") or "").strip().lower()
    pack = args.get("pack")
    try:
        limit = int(args.get("limit") or 20)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 100))
    words = query.split() if query else []
    out = []
    for e in DATA:
        if pack and e.get("pack") != pack:
            continue
        if words:
            hay = " ".join(
                str(x) for x in (e.get("name") or "", e.get("alt") or "",
                                 e.get("pack") or "", e.get("id") or "")
            ).lower()
            if not all(w in hay for w in words):
                continue
        out.append(public_record(e))
        if len(out) >= limit:
            break
    return {"count": len(out), "emojis": out}


def tool_get_emoji(args):
    e = BY_ID.get(str(args.get("id") or ""))
    if not e:
        return {"found": False, "id": str(args.get("id") or "")}
    rec = public_record(e)
    rec["found"] = True
    return rec


def tool_list_packs(args):
    counts = {}
    for e in DATA:
        counts[e.get("pack")] = counts.get(e.get("pack"), 0) + 1
    return {
        "total_emojis": len(DATA),
        "packs": [{"pack": p, "count": c} for p, c in sorted(counts.items())],
    }


TOOLS = [
    {
        "name": "search_emojis",
        "description": "Search the 2412 Telegram custom emojis by name, pack or id. "
                       "Multi-word queries use AND. Returns id, name, pack, "
                       "alt, and direct WebM/thumbnail URLs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "Search words, e.g. 'Grok', 'ChatGPT', 'heart'"},
                "pack": {"type": "string",
                         "description": "Optional exact pack name to filter by"},
                "limit": {"type": "integer", "default": 20,
                          "description": "Max results, 1-100"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_emoji",
        "description": "Get one emoji by its Telegram custom-emoji id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string",
                       "description": "Custom-emoji id, e.g. 5319288443153445517"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "list_packs",
        "description": "List all emoji packs with their emoji counts.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "search_emojis": tool_search_emojis,
    "get_emoji": tool_get_emoji,
    "list_packs": tool_list_packs,
}


def result(msg_id, payload):
    return {"jsonrpc": "2.0", "id": msg_id, "result": payload}


def error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": code, "message": message}}


def handle(msg):
    method = msg.get("method", "")
    msg_id = msg.get("id")
    if method == "initialize":
        return result(msg_id, {
            "protocolVersion": msg.get("params", {}).get("protocolVersion")
                               or "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "telegram-emoji-search", "version": "1.0.0"},
        })
    if method == "tools/list":
        return result(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params") or {}
        fn = HANDLERS.get(params.get("name"))
        if not fn:
            return error(msg_id, -32602, "unknown tool: %s" % params.get("name"))
        try:
            out = fn(params.get("arguments") or {})
        except Exception as exc:  # noqa: BLE001 - surface as tool error
            return result(msg_id, {
                "content": [{"type": "text", "text": "error: %s" % exc}],
                "isError": True,
            })
        return result(msg_id, {
            "content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}],
        })
    if method == "ping":
        return result(msg_id, {})
    # Notifications (e.g. notifications/initialized) and unknown
    # methods get no response in stdio MCP.
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
