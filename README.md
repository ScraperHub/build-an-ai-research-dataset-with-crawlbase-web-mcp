<a href="https://crawlbase.com/signup?utm_source=github&utm_medium=readme&utm_campaign=crawling_api_banner" target="_blank">
  <img src="https://github.com/user-attachments/assets/afa4f6e7-25fb-442c-af2f-b4ddcfd62ab2" 
       alt="crawling-api-cta" 
       style="max-width: 100%; border: 0;">
</a>


# AI research dataset (Crawlbase MCP)

Companion files for building a stored SaaS pricing dataset in Cursor or Codex, then querying it with natural-language prompts.

## What this folder contains

| File | Purpose |
|------|---------|
| `urls.saas-pricing.txt` | 20 public pricing URLs (one per line) |
| `prompts/01-build-dataset.txt` | Crawl and store snapshots (`store=true`) |
| `prompts/02-analyze-dataset.txt` | Comparison table across storage |
| `prompts/03-pricing-model-insights.txt` | Deeper pricing-model question |
| `prompts/04-reuse-dataset.txt` | Ask new questions without re-crawl |
| `prompts/05-cleanup-storage.txt` | Delete RIDs when done |
| `ingest_dataset.py` | Optional batch ingest via Crawling API |
| `mcp-config.sample.json` | MCP server block for Cursor / Codex |

## MCP tool mapping

| Task | MCP tools |
|------|-----------|
| Store a page | `crawl_markdown` + `store=true` |
| Count snapshots | `storage_count` |
| List RIDs | `storage_list` |
| Read one page | `storage_get` (`as=markdown`) |
| Scan many pages | `storage_bulk_get` (`as=metadata_only` or `as=markdown`) |
| Remove snapshots | `storage_delete`, `storage_bulk_delete` |

## Setup (Python ingest, optional)

```powershell
cd code
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:CRAWLBASE_TOKEN = "YOUR_CRAWLBASE_TOKEN"
python ingest_dataset.py --urls urls.saas-pricing.txt
```

macOS / Linux:

```bash
cd code
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export CRAWLBASE_TOKEN="YOUR_CRAWLBASE_TOKEN"
python ingest_dataset.py --urls urls.saas-pricing.txt
```

Writes `output/dataset-manifest.json` with RIDs and metadata (not full page bodies).

## Setup (MCP in Cursor)

1. Copy `mcp-config.sample.json` into your Cursor MCP config (project `.cursor/mcp.json` or user settings).
2. Replace `YOUR_TOKEN` and `YOUR_JS_TOKEN` with values from the [Crawlbase dashboard](https://crawlbase.com/dashboard/account/docs).
3. Restart Cursor and confirm tools such as `crawl_markdown` and `storage_list` appear.
4. Paste prompts from `prompts/` into Agent chat.

## Links

- [Crawlbase MCP on GitHub](https://github.com/crawlbase/crawlbase-mcp)
- [AI & MCP documentation](https://crawlbase.com/docs/ai)
- [Cloud Storage](https://crawlbase.com/docs/cloud-storage/)
