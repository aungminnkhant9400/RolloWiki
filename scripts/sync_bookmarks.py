#!/usr/bin/env python3
"""
RolloWiki Sync Engine
Converts RolloForge bookmarks into Obsidian wiki pages
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path("/home/ubuntu/RolloWiki")
DATA_DIR = Path("/home/ubuntu/RolloForge/data")

def load_bookmarks():
    """Load bookmarks from RolloForge"""
    with open(DATA_DIR / "bookmarks_raw.json", "r") as f:
        return json.load(f)

def load_analysis():
    """Load DeepSeek analysis results"""
    with open(DATA_DIR / "analysis_results.json", "r") as f:
        return {a["bookmark_id"]: a for a in json.load(f)}

def slugify(text):
    """Convert text to safe filename"""
    return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '-').lower()

def process_bookmark(bookmark, analysis):
    """Convert bookmark to wiki page"""
    
    # Extract concepts from tags and analysis
    concepts = analysis.get("tags", [])
    
    # Create source page
    source_file = VAULT_DIR / "02-Sources" / f"{slugify(bookmark['title'])}.md"
    
    template = f"""---
id: {bookmark['id']}
url: {bookmark['url']}
source: {bookmark.get('source', 'unknown')}
added: {bookmark.get('timestamp', datetime.now().isoformat())}
priority: {analysis.get('priority_score', 'N/A')}
bucket: {analysis.get('bucket', 'unknown')}
tags: {', '.join(concepts)}
---

# {bookmark['title']}

## Source
[Original Link]({bookmark['url']})

## Summary
{analysis.get('summary', 'No summary available')}

## Why This Matters
{analysis.get('relevance_explanation', '')}

## Actionable Items
{chr(10).join(['- [ ] ' + item for item in analysis.get('actionable_items', [])])}

## Concepts
{chr(10).join([f"- [[{c}]]" for c in concepts[:10]])}

## Personal Notes
<!-- Add your thoughts here -->

"""
    
    source_file.write_text(template)
    return source_file

def extract_concepts(bookmarks, analyses):
    """Extract and deduplicate concepts across all bookmarks"""
    concept_counts = {}
    
    for bookmark in bookmarks:
        analysis = analyses.get(bookmark["id"], {})
        for tag in analysis.get("tags", []):
            concept_counts[tag] = concept_counts.get(tag, 0) + 1
    
    # Generate concept pages for frequently mentioned topics
    for concept, count in sorted(concept_counts.items(), key=lambda x: -x[1]):
        if count >= 2:  # Only create pages for concepts with 2+ mentions
            concept_file = VAULT_DIR / "01-Concepts" / f"{slugify(concept)}.md"
            
            # Find all sources mentioning this concept
            sources = []
            for b in bookmarks:
                a = analyses.get(b["id"], {})
                if concept in a.get("tags", []):
                    sources.append(f"- [[{slugify(b['title'])}]]")
            
            template = f"""---
id: concept-{slugify(concept)}
name: {concept}
type: concept
mentions: {count}
---

# {concept.title()}

## Overview
Auto-generated concept page from {count} sources.

## Sources
{chr(10).join(sources[:20])}

## Related Concepts
<!-- Auto-linked -->

## Synthesized Insights
<!-- LLM-generated synthesis across sources -->

"""
            concept_file.write_text(template)

def sync():
    """Main sync process"""
    print("📚 Loading RolloForge data...")
    bookmarks = load_bookmarks()
    analyses = load_analysis()
    
    print(f"📝 Processing {len(bookmarks)} bookmarks...")
    
    # Process each bookmark
    for bookmark in bookmarks:
        analysis = analyses.get(bookmark["id"], {})
        process_bookmark(bookmark, analysis)
    
    # Extract concepts
    print("🔗 Extracting concepts...")
    extract_concepts(bookmarks, analyses)
    
    print(f"✅ Sync complete: {len(bookmarks)} sources, concepts generated")

if __name__ == "__main__":
    sync()
