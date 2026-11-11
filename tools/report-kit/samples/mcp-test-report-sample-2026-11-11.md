# AgentScout MCP Server Test Report (sample)

**Server:** [Microsoft Learn MCP](https://agentscouthq.com/tools/microsoft-learn-mcp.html) (`microsoft-learn-mcp`)  
**Endpoint:** `https://learn.microsoft.com/api/mcp` · Streamable HTTP · no authentication  
**Tested:** Wednesday, Nov 11, 2026, 1:00 AM PT (America/Los_Angeles)  
**Runs:** 5 (latency p50 over all runs; schema and tool-call bodies from run 1)  
**Score:** **90 / 100**

This is a sample of a paid, self-serve report a maker would receive after pasting a public MCP URL. Nothing here was published, emailed, or changed on agentscouthq.com. All protocol calls were read-only.

---

## Verdict

Microsoft Learn MCP is a strong, public, first-party server. It negotiates protocol `2025-06-18`, issues a session, lists three well-described read-only tools, and returned useful documentation and code samples on every call, in well under a second. The daily AgentScout HTTP reachability check already had this listing as live (homepage and GitHub both HTTP 200, checked Nov 10, 2026, 7:03 AM PT).

The score is not 100. The server advertises prompts and resources, then returns empty lists for both. `microsoft_docs_search` does not mark its `query` argument as required. `microsoft_docs_fetch` has no `outputSchema`, unlike the other two tools. `serverInfo` is only a name and version. Those are fixable.

---

## How this was tested

1. Reused AgentScout's existing daily MCP reachability result in `data/mcp_link_status.json` (HTTP HEAD-then-GET of the listed website and GitHub URL — this does **not** speak MCP).
2. Connected for real over Streamable HTTP: JSON-RPC `initialize`, then `notifications/initialized`, then `tools/list`, `resources/list`, and `prompts/list`.
3. Called three safe, read-only tools with harmless documentation queries. No write, send, pay, or delete tools were present or called.
4. Repeated initialize + the same three tool calls for five runs and took the median (p50) latency.
5. Linted tool schemas (descriptions, required fields, types, annotations).

Raw JSON-RPC transcript (all five runs, including full tool-call bodies):  
[`mcp-test-report-sample-2026-11-11.transcript.json`](./mcp-test-report-sample-2026-11-11.transcript.json)

Client: `agentscout-mcp-test-sample` 0.1.0. User-Agent: `AgentScoutMCPTest/0.1 (+https://agentscouthq.com/about.html)`.

---

## Scorecard

| Area | Points | Why |
|---|---:|---|
| Protocol and connectivity | 25 / 25 | Initialize HTTP 200, protocol `2025-06-18` accepted, session header set, notification accepted, 5/5 connects. |
| Correctness and reliability | 25 / 25 | 3/3 tool calls succeeded on every run. Search, fetch, and code-sample results were substantial and on-topic. Zero errors. |
| Latency | 14 / 15 | Connect p50 145 ms. Tool calls p50 273–516 ms. One `notifications/initialized` outlier at 552 ms. |
| Schema and tool quality | 16 / 20 | Excellent titles, descriptions, annotations (`readOnlyHint`, `idempotentHint`, `destructiveHint: false`). Search `query` is not required and has `"default": null`. Fetch has no `outputSchema`. |
| Capability honesty and metadata | 10 / 15 | Advertises `prompts` and `resources` with `listChanged: true`, but both lists are empty. `serverInfo` has only `name` and `version` (no title, website URL, or description). Initialize instructions themselves are excellent. |
| **Total** | **90 / 100** | |

---

## What we connected to

| | |
|---|---|
| Listed name | Microsoft Learn MCP |
| AgentScout listing | https://agentscouthq.com/tools/microsoft-learn-mcp.html |
| Website in the catalog | https://learn.microsoft.com/en-us/ |
| GitHub | https://github.com/MicrosoftDocs/mcp |
| MCP endpoint tested | https://learn.microsoft.com/api/mcp |
| Transport | Streamable HTTP (`Accept: application/json, text/event-stream`) |
| Auth | None. Public. No API key. |
| `serverInfo` | `name`: Microsoft Learn MCP Server · `version`: 1.0.0 |
| Negotiated protocol | 2025-06-18 |
| Daily HTTP check (Nov 10, 7:03 AM PT) | `url` 200, `github` 200, snapshot label **OK** |

`initialize` capabilities returned:

```json
{
  "logging": {},
  "prompts": {"listChanged": true},
  "resources": {"listChanged": true},
  "tools": {"listChanged": true}
}
```

The server also returns a long `instructions` block that correctly describes a three-step workflow: search for breadth, code-sample search for examples, fetch for depth.

---

## Latency (p50 over 5 runs, unless noted)

| Step | Latency |
|---|---|
| `initialize` (connect) | p50 **145 ms** (min 127, max 230, n=5) |
| `notifications/initialized` | p50 **174 ms** (min 115, max 552, n=5) |
| `tools/list` | p50 **171 ms** (min 171, max 171, n=1) (run 1 only) |
| `resources/list` | p50 **121 ms** (min 121, max 121, n=1) (run 1 only) |
| `prompts/list` | p50 **167 ms** (min 167, max 167, n=1) (run 1 only) |
| `tools/call` microsoft_docs_search | p50 **516 ms** (min 480, max 547, n=5) |
| `tools/call` microsoft_docs_fetch | p50 **273 ms** (min 173, max 326, n=5) |
| `tools/call` microsoft_code_sample_search | p50 **488 ms** (min 463, max 538, n=5) |

Connect and every tool call stayed under one second. That is production-quality for a documentation server.

---

## Tools, resources, prompts

**Tools: 3.** **Resources: 0.** **Prompts: 0.**

| Tool | Title | Annotations | Input | Notes |
|---|---|---|---|---|
| `microsoft_docs_search` | Microsoft Docs Search | read-only, idempotent, not destructive | `query` (string) — **not required**; `"default": null` | Has `outputSchema`. Description is detailed and tells the client to follow up with fetch. |
| `microsoft_code_sample_search` | Microsoft Code Sample Search | read-only, idempotent, not destructive | `query` required; optional `language` | Has `outputSchema`. Language enum documented in the description (csharp, python, etc.). |
| `microsoft_docs_fetch` | Microsoft Docs Fetch | read-only, idempotent, not destructive | `url` required | **No `outputSchema`.** Description states the URL must be a microsoft.com HTML docs page. |

No schema issues rose to "missing description" or "missing inputSchema". The issues are the un-required search query, the missing fetch `outputSchema`, and the advertised-but-empty prompt and resource surfaces.

---

## Tool-call results (run 1, all read-only)

| Tool | Arguments | HTTP time | Result |
|---|---|---:|---|
| `microsoft_docs_search` | `query`: "Azure Functions HTTP trigger" | 538 ms | Success. Structured results plus a ~47.5 KB payload of official Learn chunks (titles, URLs, excerpts). First hit matched the topic, including the HTTP trigger page. |
| `microsoft_docs_fetch` | `url`: `https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger` | 273 ms | Success. Full page converted to Markdown (~62.5 KB), starting at "# Azure Functions HTTP trigger". |
| `microsoft_code_sample_search` | `query`: "Azure Functions HTTP trigger C#" | 538 ms | Success. Official C# samples (~34.0 KB), including an `HttpExample` `HttpTrigger` function. |

The same three calls succeeded on runs 2–5 with no errors. Search and code-sample results are returned both as stringified JSON inside `content[].text` and as `structuredContent`. Fetch returns Markdown in `content` only.

---

## Schema and quality issues

1. **Prompts and resources are advertised, then empty.** `initialize` capabilities include `prompts.listChanged` and `resources.listChanged`, but `prompts/list` and `resources/list` both returned `{"prompts": []}` / `{"resources": []}` with HTTP 200. Clients may offer empty menus, or assume list-changed notifications that never matter. Either ship a couple of real prompts (for example "Search Microsoft docs" and "Fetch a Learn page") and a resource template for Learn URLs, or drop those capabilities until they have something to list.
2. **`microsoft_docs_search` does not require `query`.** The property exists and is well described, but it is omitted from `required` and is given `"default": null`. A client can legally call the tool with no query. The other two tools correctly require their main argument.
3. **`microsoft_docs_fetch` has no `outputSchema`.** Search and code-sample search both declare one. Fetch is the tool that returns the largest body, and it only has unstructured `content`. Adding a schema (for example Markdown text plus the canonical URL) would make this consistent and easier for typed clients.
4. **`serverInfo` is thin.** Only `name` and `version`. Context7, by comparison, also returns `title`, `websiteUrl`, and `description` on initialize. A website URL here should be `https://learn.microsoft.com/` (or the GitHub repo). Optional icons would help MCP client UIs.
5. **Search results are double-encoded as text.** The `content[0].text` value is a JSON string of the same results already present in `structuredContent`. Harmless, but messier for clients that only read text content.

Issue 4 and 5 did not cost as many points as 1–3. They are still worth fixing.

---

## Top 3 fixes

1. **Mark `query` as required on `microsoft_docs_search`, and remove `"default": null`.** One-line schema change. Prevents empty searches and matches the other two tools.
2. **Stop advertising empty surfaces — or fill them.** Add one or two prompts that wrap the documented workflow, and/or a Learn-page resource template. If that is out of scope, omit `prompts` and `resources` from `initialize` capabilities so clients do not list empty categories.
3. **Add `outputSchema` to `microsoft_docs_fetch`, and enrich `serverInfo`** with `title`, `websiteUrl`, and a one-line `description`. Small metadata change, clearer for registries, catalogs, and typed clients.

---

## Reproducible commands

These speak MCP. They do not submit anything, and they only read documentation.

```bash
# 1. initialize (expect HTTP 200, text/event-stream, mcp-session-id)
curl -sS -D - -o /tmp/mslearn-init.sse \
  -X POST 'https://learn.microsoft.com/api/mcp' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  -H 'MCP-Protocol-Version: 2025-06-18' \
  -H 'User-Agent: AgentScoutMCPTest/0.1 (+https://agentscouthq.com/about.html)' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"agentscout-mcp-test-sample","version":"0.1.0"}}}'

# 2. notifications/initialized (send the session header from step 1)
# 3. tools/list, resources/list, prompts/list
# 4. tools/call (examples used in this report)
#    microsoft_docs_search              {"query":"Azure Functions HTTP trigger"}
#    microsoft_docs_fetch               {"url":"https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger"}
#    microsoft_code_sample_search       {"query":"Azure Functions HTTP trigger C#"}
```

The script that produced the five-run transcript and this score is saved at `/tmp/mcp-probe/mcp_http_client.py` on the AgentScout box. The JSON-RPC transcript beside this report is the source of every latency number and schema claim above.

Shortened initialize + list excerpt from run 1 (tool-call bodies omitted; see the transcript file):

```json
[
  {
    "http_status": 200,
    "http_ms": 216.9,
    "request": {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "initialize",
      "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {
          "name": "agentscout-mcp-test-sample",
          "version": "0.1.0"
        }
      }
    },
    "messages": [
      {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
          "protocolVersion": "2025-06-18",
          "capabilities": {
            "logging": {},
            "prompts": {
              "listChanged": true
            },
            "resources": {
              "listChanged": true
            },
            "tools": {
              "listChanged": true
            }
          },
          "serverInfo": {
            "name": "Microsoft Learn MCP Server",
            "version": "1.0.0"
          },
          "instructions": "# Microsoft Learn MCP Server\r\n\r\nThis server gives structured access to official Microsoft and Azure documentation via three tools:\r\n\r\n## Tools\r\n\r\n### microsoft_docs_search\r\nSearch \u2026"
        }
      }
    ]
  },
  {
    "http_status": 202,
    "http_ms": 174.5,
    "request": {
      "jsonrpc": "2.0",
      "method": "notifications/initialized"
    },
    "messages": []
  },
  {
    "http_status": 200,
    "http_ms": 171.0,
    "request": {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/list",
      "params": {}
    },
    "messages": [
      {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
          "tools": "[3 tools \u2014 see full transcript]"
        }
      }
    ]
  },
  {
    "http_status": 200,
    "http_ms": 120.7,
    "request": {
      "jsonrpc": "2.0",
      "id": 3,
      "method": "resources/list",
      "params": {}
    },
    "messages": [
      {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
          "resources": []
        }
      }
    ]
  },
  {
    "http_status": 200,
    "http_ms": 167.0,
    "request": {
      "jsonrpc": "2.0",
      "id": 4,
      "method": "prompts/list",
      "params": {}
    },
    "messages": [
      {
        "jsonrpc": "2.0",
        "id": 4,
        "result": {
          "prompts": []
        }
      }
    ]
  }
]
```

---

## What this sample does not include

- Authenticated or paid MCP servers (OAuth, API keys, x402).
- stdio / `npx` servers (not needed here; this endpoint is public HTTP).
- Write-path or destructive tool calls (none were offered).
- Changing the AgentScout daily check, the listing page, or Microsoft's server.

The existing daily check only requests the listed website and GitHub URL over HTTP. This report is the protocol-level step that a self-serve product would add on top.

---

*AgentScout sample · Nov 11, 2026 · not sent to the maker · not published*
