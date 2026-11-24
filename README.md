# Public API Docs MCP

A read-only MCP server for API documentation published with [Hoppscotch](https://docs.hoppscotch.io/documentation/features/documentation) or [Postman](https://learning.postman.com/docs/publishing-your-api/publishing-your-docs/). Search requests, inspect endpoint details, and read saved response examples. It uses each provider's public documentation endpoint; no account or token is required.

## Installation

### For Agents

Copy one of these prompts and paste it into your MCP-capable AI agent.

#### Using uv

```text
Install the Public API Docs MCP server for this AI client from https://github.com/KidiXDev/public-api-docs-mcp.

Follow the repository README and install it using uv. Install uv first if needed.

Configure this client to run:
public-api-docs-mcp

Do not set a default document URL. I will give you a published URL for each project; pass it as doc_url on every tool call.

Verify that the server exposes get_document, search_documentation, list_endpoints, and get_endpoint.

Tell me what you configured and whether I need to restart the client.
```

#### Using Docker

```text
Install the Public API Docs MCP server for this AI client from https://github.com/KidiXDev/public-api-docs-mcp.

Use the prebuilt Docker image:
ghcr.io/kidixdev/public-api-docs-mcp:latest

Configure this client to run the MCP server over stdio using:
docker run --rm -i ghcr.io/kidixdev/public-api-docs-mcp:latest

Do not set a default document URL. I will give you a published URL for each project; pass it as doc_url on every tool call.

Verify that the server exposes get_document, search_documentation, list_endpoints, and get_endpoint.

Tell me what you configured and whether I need to restart the client.
```

### For Humans

#### Using uv

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

Install directly from GitHub:

```bash
uv tool install git+https://github.com/KidiXDev/public-api-docs-mcp.git
```

Or install from a checkout:

```bash
uv tool install .
```

Then [configure your MCP client](#manual-mcp-client-setup).

To check a published document:

```bash
public-api-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

If the command is not found after installation, run `uv tool update-shell`, reopen your terminal, or use the executable's absolute path in your MCP client.

#### Using Docker

Pull the prebuilt image:

```bash
docker pull ghcr.io/kidixdev/public-api-docs-mcp:latest
```

Check a published document:

```bash
docker run --rm \
  ghcr.io/kidixdev/public-api-docs-mcp:latest \
  --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

For an MCP client's stdio configuration, use:

```bash
docker run --rm -i ghcr.io/kidixdev/public-api-docs-mcp:latest
```

Keep `-i` and do not detach the container.

## Choose a document per call

Start the server without a document URL. Pass the project's published link as `doc_url` on each tool call:

| Provider | Link |
| --- | --- |
| Hoppscotch | `https://api-docs.hoppscotch.io/view/<slug>[/<version>]` |
| Postman | `https://documenter.getpostman.com/view/<owner>/<id>`, optionally with `?version=<tag>` or a `#<request-id>` deep link |

For example:

```text
search_documentation(
  query="tenant",
  doc_url="https://api-docs.hoppscotch.io/view/YOUR_DOC_ID"
)
```

Include the relevant URL in your request to the agent so it can pass the right URL for each project.

Without a document URL, a tool call returns an error. Postman custom domains, private workspaces, and `postman.com` workspace links are not supported.

For compatible self-hosted Hoppscotch deployments, these optional settings change where the server reads published docs:

| Variable                  | Purpose                                                 | Default                          |
| ------------------------- | ------------------------------------------------------- | -------------------------------- |
| `HOPPSCOTCH_DOCS_ORIGIN`  | Allowed public viewer origin                            | `https://api-docs.hoppscotch.io` |
| `HOPPSCOTCH_API_BASE_URL` | Backend base URL for compatible self-hosted deployments | `https://api.hoppscotch.io/v1`   |

For a self-hosted deployment using the same `/v1/published-docs` route, set both values to that deployment's viewer origin and backend `/v1` URL.

Per-call Hoppscotch `doc_url` values must match the configured viewer origin. Postman links are unaffected.

## MCP tools

| Tool | What it returns |
| --- | --- |
| `search_documentation(query, doc_url="", offset=0, limit=10)` | Ranked, short endpoint summaries for an API concept; up to 50 per page |
| `get_endpoint(request_id, doc_url="", response_name="", full_bodies=False)` | One endpoint's request details, its saved responses, and one example response |
| `get_document(doc_url="")` | Title, versions, description, folder paths with endpoint counts, variable names, and endpoint count |
| `list_endpoints(folder="", method="", query="", doc_url="", offset=0, limit=50)` | Endpoints in document order, filtered by folder, method, or exact text; up to 100 per page |

The server sends this workflow to the agent as MCP instructions:

1. Search one concept at a time (`product`, then `tenant`) with `search_documentation`. Search uses keyword ranking, not semantic understanding. To cover a whole API, use `get_document`, then `list_endpoints` by folder.
2. Call `get_endpoint` for the routes the task needs. It includes the first 2xx example response.
3. Call it again with a `response_name` for other cases, such as errors.

Search and list results include `total` and `next_offset` for paging. `get_endpoint` shortens strings over 300 characters and arrays over three items in bodies, keeps the JSON structure, and reports `body_truncated` and `response.truncated`. Pass `full_bodies=true` for the uncut content. Fetched documents are cached for up to a minute.

The server omits saved auth and variable values and redacts credential-like header and parameter values. Descriptions and request and response bodies are otherwise returned as published, so review the source document before sharing its contents.

## Manual MCP client setup

These configurations start a **stdio** server without selecting a project.

Give your agent the published URL for the project you are working on; it passes that URL as `doc_url` when calling tools.

The server normally prints nothing in a terminal because it exchanges protocol messages over stdin/stdout.

The examples below use the `uv` installation.

If you use Docker, replace the executable with:

```json
{
  "command": "docker",
  "args": [
    "run",
    "--rm",
    "-i",
    "ghcr.io/kidixdev/public-api-docs-mcp:latest"
  ]
}
```

### Codex

Add this to `~/.codex/config.toml` or a project `.codex/config.toml`:

```toml
[mcp_servers.api_docs]
command = "public-api-docs-mcp"
```

Run:

```bash
codex mcp list
```

See the [Codex MCP guide](https://developers.openai.com/codex/mcp).

### Claude Code

```bash
claude mcp add --scope user --transport stdio api-docs -- public-api-docs-mcp
claude mcp get api-docs
```

See the [Claude Code MCP guide](https://code.claude.com/docs/en/mcp).

For **Claude Desktop**, edit `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows, then fully restart the app:

```json
{
  "mcpServers": {
    "api-docs": {
      "command": "public-api-docs-mcp"
    }
  }
}
```

Use the command's absolute path if Claude Desktop cannot find it.

See the [MCP Python SDK host guide](https://py.sdk.modelcontextprotocol.io/v2/get-started/real-host/).

### Google Antigravity

In the IDE, open:

```text
MCP Servers → Manage MCP Servers → View raw config
```

In Antigravity CLI, edit `~/.gemini/config/mcp_config.json` or `.agents/mcp_config.json` in a workspace:

```json
{
  "mcpServers": {
    "api-docs": {
      "command": "public-api-docs-mcp"
    }
  }
}
```

See the [Antigravity MCP guide](https://antigravity.google/docs/mcp).

### GitHub Copilot

For Copilot in VS Code, create `.vscode/mcp.json` in your project or use **MCP: Open User Configuration**:

```json
{
  "servers": {
    "api-docs": {
      "type": "stdio",
      "command": "public-api-docs-mcp"
    }
  }
}
```

Use Copilot Chat **Agent** mode and enable the server in its tools picker.

For Copilot CLI:

```bash
copilot mcp add api-docs -- public-api-docs-mcp
copilot mcp get api-docs
```

The CLI also accepts a portable `~/.copilot/mcp-config.json` with a top-level `mcpServers` object. VS Code's `.vscode/mcp.json` uses `servers`.

See [VS Code's MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) and the [Copilot CLI MCP guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers).

## HTTP transport

To run an HTTP server locally with Docker:

```bash
docker run --rm \
  -p 127.0.0.1:8000:8000 \
  ghcr.io/kidixdev/public-api-docs-mcp:latest \
  --http \
  --host 0.0.0.0
```

Connect a Streamable HTTP MCP client to:

```text
http://127.0.0.1:8000/mcp
```

Pass `doc_url` to each tool call.

For a local Python process:

```bash
public-api-docs-mcp --http
```

## Develop

```bash
uv run python -m unittest -v
uv run public-api-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

Build the Docker image locally:

```bash
docker build -t public-api-docs-mcp .
```

## License

This project is licensed under [MIT](LICENSE).
