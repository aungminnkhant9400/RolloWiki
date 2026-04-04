#!/usr/bin/env python3
"""
RolloWiki AI Synthesizer (Enhanced with LLM)
Generates intelligent insights by reading and analyzing multiple sources
"""

import json
import os
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

def generate_llm_synthesis(concept_name, related_sources):
    """
    Use Kimi API to generate real synthesis from multiple sources
    """
    if len(related_sources) < 2:
        return None
    
    # Build prompt
    sources_text = "\n\n---\n\n".join([
        f"Source {i+1}: {s['title']}\nSummary: {s['summary']}\nKey Insights: {chr(10).join(s['insights'][:3])}"
        for i, s in enumerate(related_sources[:5])  # Top 5 sources
    ])
    
    prompt = f"""You are a research assistant analyzing multiple sources about "{concept_name}".

Read these sources and synthesize:
1. What are the common themes across all sources?
2. What are the contradictions or different perspectives?
3. What are the actionable recommendations?
4. What questions remain unanswered?

Keep it concise (max 300 words). Be specific, not generic.

SOURCES:
{sources_text}

SYNTHESIS:"""

    # Write prompt to file for subagent processing
    prompt_file = VAULT_DIR / ".synthesis_prompt.txt"
    prompt_file.write_text(prompt)
    
    return prompt_file

def synthesize_concept_with_llm(concept_name, bookmarks, analyses):
    """Generate AI-powered synthesis for a concept"""
    
    # Find all bookmarks tagged with this concept
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
        return None
    
    # Sort by priority
    related.sort(key=lambda x: -x['priority'])
    
    # Generate LLM prompt
    prompt_file = generate_llm_synthesis(concept_name, related)
    
    # Create a marker file that tells the system to run LLM synthesis
    marker = VAULT_DIR / ".pending_llm_synthesis"
    
    synthesis_request = {
        "concept": concept_name,
        "sources_count": len(related),
        "prompt_file": str(prompt_file),
        "timestamp": datetime.now().isoformat()
    }
    
    # Append to pending list
    pending = []
    if marker.exists():
        try:
            pending = json.loads(marker.read_text())
        except:
            pass
    
    pending.append(synthesis_request)
    marker.write_text(json.dumps(pending, indent=2))
    
    return len(related)

def generate_all_syntheses():
    """Queue LLM syntheses for all concepts"""
    print("🧠 Loading bookmark data...")
    bookmarks = load_bookmarks()
    analyses = load_analysis()
    
    concepts_dir = VAULT_DIR / "01-Concepts"
    queued = 0
    
    print("📝 Queueing LLM syntheses...")
    for concept_file in concepts_dir.glob("*.md"):
        concept_name = concept_file.stem
        
        count = synthesize_concept_with_llm(concept_name, bookmarks, analyses)
        if count:
            print(f"  ✓ {concept_name}: {count} sources → queued for LLM synthesis")
            queued += 1
    
    if queued > 0:
        print(f"\n🚀 {queued} concepts queued for LLM synthesis")
        print("Run: ./scripts/run_llm_synthesis.sh to process")
    else:
        print("\n✅ No new syntheses needed")
    
    return queued

if __name__ == "__main__":
    generate_all_syntheses()
