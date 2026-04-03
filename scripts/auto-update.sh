#!/bin/bash
# RolloWiki Auto-Update
# Run this to sync new bookmarks, re-link concepts, re-synthesize, and push to GitHub

cd /home/ubuntu/RolloWiki

echo "🔄 RolloWiki Auto-Update"
echo "========================"

# 1. Sync new bookmarks from RolloForge
echo "📚 Syncing bookmarks..."
python3 scripts/sync_bookmarks.py

# 2. Auto-link related concepts
echo "🔗 Linking concepts..."
python3 scripts/linker.py

# 3. Re-synthesize insights
echo "🧠 Synthesizing..."
python3 scripts/synthesizer.py

# 4. Check for changes
if git diff --quiet; then
    echo "✅ No new changes to push"
    exit 0
fi

# 5. Commit and push
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M') - sync, link, synthesize"
git push origin main

echo "✅ RolloWiki updated and synced!"
echo "Pull on your Windows machine: git pull"
