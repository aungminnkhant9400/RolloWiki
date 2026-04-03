# RolloWiki

LLM-powered knowledge base system integrating RolloForge bookmarks with personal data analysis.

## Based On

- **Karpathy's System:** LLM-generated wiki from diverse sources (articles, papers, datasets)
- **0xSero's Approach:** Personal data integration with OpenClaw for self-analysis

## Vault Structure

```
RolloWiki/
├── 00-Inbox/           # New bookmarks pending synthesis
├── 01-Concepts/        # Extracted concepts (auto-generated)
├── 02-Sources/         # Source bookmarks from RolloForge
├── 03-Synthesized/     # LLM-generated wiki pages
├── 04-Personal/        # Personal data analysis & insights
└── 99-Indices/         # Auto-generated indexes
```

## Workflow

1. **Ingest:** RolloForge captures new bookmarks → 00-Inbox
2. **Extract:** LLM extracts concepts → 01-Concepts
3. **Link:** Auto-connect related concepts
4. **Synthesize:** Generate wiki pages → 03-Synthesized
5. **Personal:** Add self-analysis from personal data → 04-Personal

## Sync

Run `./scripts/sync.sh` to sync with RolloForge.
