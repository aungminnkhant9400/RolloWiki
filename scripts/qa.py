#!/usr/bin/env python3
"""
RolloWiki Q&A Interface
Ask questions about your bookmarks, get AI-synthesized answers
"""

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = Path("/home/ubuntu/RolloForge/data")

def load_data():
    """Load all bookmark data"""
    with open(DATA_DIR / "bookmarks_raw.json") as f:
        bookmarks = json.load(f)
    with open(DATA_DIR / "analysis_results.json") as f:
        analyses = {a["bookmark_id"]: a for a in json.load(f)}
    return bookmarks, analyses

def search_bookmarks(bookmarks, analyses, query):
    """Find relevant bookmarks for a query"""
    query_words = set(query.lower().split())
    
    scored = []
    for b in bookmarks:
        analysis = analyses.get(b["id"], {})
        
        # Build searchable text
        text = (
            b.get("title", "") + " " +
            analysis.get("summary", "") + " " +
            " ".join(analysis.get("tags", [])) + " " +
            " ".join(analysis.get("key_insights", []))
        ).lower()
        
        # Score by keyword matches
        matches = sum(1 for word in query_words if word in text)
        
        # Bonus for exact phrase match
        if query.lower() in text:
            matches += 5
        
        # Bonus for priority
        priority = analysis.get("priority_score", 0)
        
        total_score = matches + (priority / 10)
        
        if matches > 0:
            scored.append({
                "bookmark": b,
                "analysis": analysis,
                "score": total_score,
                "matched": matches
            })
    
    # Sort by score
    scored.sort(key=lambda x: -x["score"])
    return scored[:10]  # Top 10

def format_sources(results):
    """Format sources for LLM prompt"""
    sources_text = []
    for i, r in enumerate(results[:5], 1):
        a = r["analysis"]
        sources_text.append(
            f"Source {i}: {r['bookmark']['title'][:80]}\n"
            f"Summary: {a.get('summary', '')[:300]}\n"
            f"Key Insights: {'; '.join(a.get('key_insights', [])[:3])}\n"
            f"Priority: {a.get('priority_score', 'N/A')}"
        )
    return "\n\n---\n\n".join(sources_text)

def generate_answer(query, results):
    """Generate prompt for LLM synthesis"""
    if not results:
        return "No relevant bookmarks found for this query."
    
    sources_text = format_sources(results)
    
    prompt = f"""Based on the user's bookmarks, answer this question:

QUESTION: {query}

RELEVANT BOOKMARKS:
{sources_text}

Provide a concise answer that:
1. Synthesizes key insights from the bookmarks
2. Highlights agreements or contradictions
3. Gives actionable recommendations
4. Cites specific sources

Keep it under 200 words. Be specific, not generic."""

    return prompt

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 qa.py 'your question'")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"🔍 Searching: '{query}'\n")
    
    bookmarks, analyses = load_data()
    results = search_bookmarks(bookmarks, analyses, query)
    
    if not results:
        print("❌ No relevant bookmarks found.")
        return
    
    print(f"✅ Found {len(results)} relevant bookmarks\n")
    
    # Generate LLM prompt
    answer_prompt = generate_answer(query, results)
    
    # Save prompt for LLM processing
    prompt_file = Path("/home/ubuntu/RolloWiki/.qa_prompt.txt")
    prompt_file.write_text(answer_prompt)
    
    print("🧠 LLM prompt generated. Run this to get the answer:")
    print(f"openclaw chat complete --model kimi/kimi-code --message-file {prompt_file}")
    
    # Also show quick summary
    print("\n📚 Quick Summary of Top Sources:")
    for i, r in enumerate(results[:3], 1):
        print(f"{i}. {r['bookmark']['title'][:60]}... (Priority: {r['analysis'].get('priority_score', 'N/A')})")

if __name__ == "__main__":
    main()
