# Telegram Emoji Search — MCP server

Use the 2,412 emojis as an MCP server, so an AI client can search them
with tools instead of you pasting data.

## What it exposes

| Tool | What it does |
| --- | --- |
| `search_emojis(query, pack?, limit?)` | Search by name / pack / id, multi-word AND. Returns id, name, pack, alt, `webm_url`, `thumb_url`. |
| `get_emoji(id)` | One emoji by its Telegram custom-emoji id. |
| `list_packs()` | All packs with counts. |

Links point at the GitHub Pages site, e.g.
`https://winhtundev.github.io/telegram-emoji-search/webm/<pack>/<id>.webm`

No dependencies — Python 3 standard library only. It reads `emojis.json`
next to the script (override with the `EMOJI_JSON` env var, or pass the
path as the first argument).

## Run it

```bash
python3 mcp_server.py
```

It speaks MCP over stdio (JSON-RPC, one message per line).

## Connect it

### Muse / Claude Desktop (`mcpServers` config)

```json
{
  "mcpServers": {
    "telegram-emoji-search": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp_server.py"],
      "env": {}
    }
  }
}
```

Clone the repo first, then use the real path to `mcp_server.py`
(`emojis.json` must sit next to it).

### Quick test from a terminal

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_emojis","arguments":{"query":"Grok"}}}' \
  | python3 mcp_server.py
```

You should get the tools list, then the Grok results.

## Notes

- The Pages site itself is for humans browsing; this script is what makes
  the same data usable as MCP.
- A Telegram custom emoji still needs its id in a Bot API message to
  render as a real custom emoji — MCP returns that id, it does not render
  it by itself.
- For a Mini App web page, play the `webm_url` with
  `<video autoplay loop muted playsinline>`, with the thumbnail as fallback.
