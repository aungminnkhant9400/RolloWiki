#!/usr/bin/env python3
"""
RolloWiki LLM Synthesis Engine
Uses Kimi API to generate intelligent insights from multiple sources
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

VAULT_DIR = Path("/home/ubuntu/RolloWiki")
DATA_DIR = Path("/home/ubuntu/RolloForge/data")

def load_bookmarks():
    with open(DATA_DIR / "bookmarks_raw.json") as f:
        return json.load(f)

def load_analysis():
    with open(DATA_DIR / "analysis_results.json") as f:
        return {a["bookmark_id"]: a for a in json.load(f)}

def spawn_llm_synthesis(concept_name, sources):
    """
    Spawn a subagent to run LLM synthesis
    """
    if len(sources) < 2:
        return None
    
    # Build sources text
    sources_text = "\n\n---\n\n".join([
        f"Source {i+1}: {s['title']}\nSummary: {s['summary'][:300]}...\nKey Points: {', '.join(s['insights'][:2])}"
        for i, s in enumerate(sources[:4])
    ])
    
    prompt = f"""Synthesize insights about '{concept_name}' from these {len(sources)} sources:

{sources_text}

Provide:
1. **Key Themes** (2-3 sentences on what sources agree on)
2. **Contradictions** (if any sources disagree)
3. **Actionable Insights** (specific recommendations)
4. **Open Questions** (what's still unclear)

Be concise but specific. Write like a research analyst, not a chatbot.

Save this synthesis to: /home/ubuntu/RolloWiki/01-Concepts/{concept_name}.md
Append it under "## AI Synthesis" section."""

    # Create subagent spawn command
    result = subprocess.run([
        "openclaw", "sessions", "spawn",
        "--label", f"synthesize-{concept_name}",
        "--mode", "run",
        "--runtime", "subagent",
        "--timeout", "1800",
        "--", "python3", "-c",
        f"""
import json
from pathlib import Path

# Read the concept file
concept_file = Path("/home/ubuntu/RolloWiki/01-Concepts/{concept_name}.md")
content = concept_file.read_text()

# Generate synthesis using Kimi via OpenClaw
import subprocess
result = subprocess.run([
    "openclaw", "chat", "complete",
    "--model", "kimi/kimi-code",
    "--message", {json.dumps(prompt)}
], capture_output=True, text=True)

synthesis = result.stdout if result.returncode == 0 else "LLM synthesis failed."

# Update the file
if "## AI Synthesis" in content:
    # Replace existing
    import re
    new_section = "## AI Synthesis\n\n" + synthesis + "\n\n*Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "*"
    content = re.sub(r'## AI Synthesis.*?(?=\n## |\Z)', new_section, content, flags=re.DOTALL)
else:
    content = content.rstrip() + "\n\n## AI Synthesis\n\n" + synthesis + "\n\n*Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "*"

concept_file.write_text(content)
print(f"✓ Synthesized {concept_name}")
"""
    ], capture_output=True, text=True)
    
    return result.returncode == 0

def process_concept(concept_name, bookmarks, analyses):
    """Find sources and queue synthesis for a concept"""
    
    related = []
    for b in bookmarks:
        analysis = analyses.get(b["id"], {})
        tags = analysis.get("tags", [])
        if concept_name.replace('-', ' ') in tags or concept_name in tags:
            related.append({
                'title': b['title'],
                'summary': analysis.get('summary', ''),
                'insights': analysis.get('key_insights', []),
                'priority': analysis.get('priority_score', 0)
            })
    
    if len(related) < 2:
        return 0
    
    related.sort(key=lambda x: -x['priority'])
    
    # For now, just process top concepts
    if spawn_llm_synthesis(concept_name, related):
        return len(related)
    return 0

def main():
    print("🧠 RolloWiki LLM Synthesis Engine")
    print("=" * 40)
    
    bookmarks = load_bookmarks()
    analyses = load_analysis()
    
    concepts_dir = VAULT_DIR / "01-Concepts"
    processed = 0
    
    # Process concepts with most sources first
    concept_sources = []
    for concept_file in concepts_dir.glob("*.md"):
        concept_name = concept_file.stem
        count = sum(1 for b in bookmarks 
                   if concept_name.replace('-', ' ') in 
                   analyses.get(b["id"], {}).get("tags", []))
        concept_sources.append((concept_name, count))
    
    concept_sources.sort(key=lambda x: -x[1])
    
    # Process top 3 concepts
    for concept_name, count in concept_sources[:3]:
        if count >= 2:
            print(f"\n📝 Synthesizing: {concept_name} ({count} sources)")
            processed += process_concept(concept_name, bookmarks, analyses)
    
    print(f"\n✅ Queued {processed} concepts for LLM synthesis")
    print("Subagents will process these in the background.")

if __name__ == "__main__":
    main()
