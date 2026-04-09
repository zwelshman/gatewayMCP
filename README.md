# HDRUK Health Data Research Gateway — MCP Server

An MCP (Model Context Protocol) server that exposes the public [Health Data Research UK Gateway](https://healthdatagateway.org) REST API as tools for Claude or any MCP client.

## What it does

Gives Claude (or any MCP host) the ability to search and browse:

| Tool | Description |
|------|-------------|
| `search_datasets` | Search NHS / academic datasets with keyword, date, custodian filters |
| `get_dataset` | Full metadata for a specific dataset by ID |
| `search_collections` | Search Collections / Networks grouped by theme or disease |
| `get_collection` | Full details + all linked resources for a collection |
| `search_data_uses` | Search approved research projects that accessed specific data |
| `get_data_use` | Full data use record by ID |
| `search_publications` | Search peer-reviewed papers linked to Gateway datasets |
| `search_tools` | Search reusable analysis scripts, phenotyping algorithms, pipelines |
| `search_data_custodians` | Search data custodians (NHS England, SAIL, CPRD, etc.) |
| `get_data_custodian` | Full custodian profile by ID |
| `search_all` | Global cross-entity search across all types at once |
| `get_dataset_linked_resources` | All publications, tools, data uses and collections linked to a dataset |

## Installation

```bash
# 1. Clone / copy the server
git clone <your-repo-url>
cd hdruk-gateway-mcp

# 2. Install dependencies (Python 3.10+)
pip install fastmcp httpx

# 3. Run the server
python server.py
```

## Claude Code / claude.json configuration

Add to `~/.claude.json` (or project-level `.claude/claude.json`):

```json
{
  "mcpServers": {
    "hdruk-gateway": {
      "type": "stdio",
      "command": "python",
      "args": ["/absolute/path/to/hdruk-gateway-mcp/server.py"]
    }
  }
}
```

Or if installed as a package:

```json
{
  "mcpServers": {
    "hdruk-gateway": {
      "type": "stdio",
      "command": "hdruk-gateway-mcp"
    }
  }
}
```

## Claude Desktop (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "hdruk-gateway": {
      "command": "python",
      "args": ["/absolute/path/to/hdruk-gateway-mcp/server.py"]
    }
  }
}
```

## Example prompts once connected

```
Find all datasets related to cardiovascular disease in the HDRUK Gateway

Search the Gateway for BHF Data Science Centre collections

Show me data uses / research projects that used HES APC data

What publications have been linked to the GDPPR dataset?

Find phenotyping tools or scripts on the Gateway for atrial fibrillation

Get full metadata for dataset ID 888
```

## API details

- **Base URL**: `https://api.healthdatagateway.org/api/v2/`
- **Authentication**: None required for read operations
- **Rate limits**: Please be respectful; avoid tight loops of requests
- **Source**: [HDRUK/gateway-api](https://github.com/HDRUK/gateway-api) (Apache 2.0)

## Notes for BHF DSC / SAIL users

- Collections of interest: search for `"BHF Data Science Centre"`, `"SAIL"`, or `"Secure Data Environment"`
- Useful dataset IDs from your work: GDPPR, HES APC/OP/AE, CPRD GOLD/Aurum, SAIL WLGP/PEDW
- The `search_all` tool is good for a first pass; then use specific tools to drill down
- `get_dataset_linked_resources` is handy for checking what phenotyping papers exist for a dataset

## Project structure

```
hdruk-gateway-mcp/
├── server.py          # Main MCP server — all tools defined here
├── pyproject.toml     # Package metadata and dependencies
└── README.md          # This file
```
