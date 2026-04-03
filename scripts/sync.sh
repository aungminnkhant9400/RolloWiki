#!/bin/bash
# Sync RolloWiki with RolloForge bookmarks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="/home/ubuntu/RolloForge/data"

echo "🔄 Syncing RolloWiki with RolloForge..."

# Check for new bookmarks
python3 "$SCRIPT_DIR/sync_bookmarks.py"

echo "✅ Sync complete"
