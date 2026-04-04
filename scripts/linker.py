#!/usr/bin/env python3
"""
RolloWiki Linker
Finds semantically related concepts and auto-links them
"""

import json
import re
from pathlib import Path
from collections import defaultdict

VAULT_DIR = Path("/home/ubuntu/RolloWiki")
DATA_DIR = Path("/home/ubuntu/RolloForge/data")

def load_concepts():
    """Load all concept pages"""
    concepts_dir = VAULT_DIR / "01-Concepts"
    concepts = {}
    for f in concepts_dir.glob("*.md"):
        content = f.read_text()
        # Extract concept name from frontmatter or filename
        name = f.stem.replace('-', ' ')
        concepts[name] = {
            'file': f,
            'content': content,
            'sources': extract_sources(content)
        }
    return concepts

def extract_sources(content):
    """Extract linked sources from content"""
    sources = re.findall(r'\[\[([^\]]+)\]\]', content)
    return sources

def find_related_concepts(concepts, target_concept, threshold=0.3):
    """
    Find concepts related by shared sources
    Returns: list of (concept_name, shared_count, jaccard_score)
    """
    target = concepts.get(target_concept)
    if not target:
        return []
    
    target_sources = set(target['sources'])
    if not target_sources:
        return []
    
    related = []
    for name, data in concepts.items():
        if name == target_concept:
            continue
        
        other_sources = set(data['sources'])
        if not other_sources:
            continue
        
        shared = target_sources & other_sources
        if len(shared) >= 1:  # At least 1 shared source
            # Jaccard similarity
            jaccard = len(shared) / len(target_sources | other_sources)
            if jaccard >= threshold:
                related.append((name, len(shared), round(jaccard, 2)))
    
    return sorted(related, key=lambda x: -x[1])  # Sort by shared count

def update_concept_links():
    """Update all concept pages with related links"""
    concepts = load_concepts()
    
    for name, data in concepts.items():
        related = find_related_concepts(concepts, name)
        
        if related:
            # Generate related concepts section
            links_section = "\n## Related Concepts (Auto-Linked)\n\n"
            for rel_name, shared, jaccard in related[:5]:  # Top 5
                rel_slug = rel_name.replace(' ', '-')
                links_section += f"- [[{rel_slug}]] (shared {shared} sources, similarity: {jaccard})\n"
            
            # Update file content
            content = data['content']
            # Replace or append the related concepts section
            if "## Related Concepts" in content:
                content = re.sub(
                    r'## Related Concepts.*?(?=\n## |\Z)',
                    links_section,
                    content,
                    flags=re.DOTALL
                )
            else:
                content = content.rstrip() + "\n" + links_section
            
            data['file'].write_text(content)
            print(f"  Updated: {name} ({len(related)} related concepts)")

def link_sources_to_concepts():
    """Add concept links to source pages based on tags"""
    sources_dir = VAULT_DIR / "02-Sources"
    concepts_dir = VAULT_DIR / "01-Concepts"
    
    # Get list of all concepts
    concept_names = set(f.stem for f in concepts_dir.glob("*.md"))
    
    updated = 0
    for source_file in sources_dir.glob("*.md"):
        content = source_file.read_text()
        
        # Extract tags from frontmatter
        tags_match = re.search(r'tags:\s*(.+)', content)
        if not tags_match:
            continue
        
        tags_line = tags_match.group(1)
        tags = [t.strip() for t in tags_line.split(',')]
        
        # Find matching concepts
        new_links = []
        for tag in tags:
            tag_slug = tag.replace(' ', '-')
            if tag_slug in concept_names:
                if f"[[{tag_slug}]]" not in content:
                    new_links.append(f"[[{tag_slug}]]")
        
        if new_links:
            # Add to concepts section
            if "## Concepts" in content:
                # Append to existing concepts section
                content = content.replace(
                    "## Concepts",
                    "## Concepts\n" + "\n".join(f"- {link}" for link in new_links)
                )
            else:
                # Add before personal notes
                content = content.replace(
                    "## Personal Notes",
                    "## Concepts\n" + "\n".join(f"- {link}" for link in new_links) + "\n\n## Personal Note"
                )
            
            source_file.write_text(content)
            updated += 1
    
    print(f"  Updated {updated} source pages with concept links")

if __name__ == "__main__":
    print("🔗 Auto-linking concepts...")
    update_concept_links()
    print("\n🔗 Linking sources to concepts...")
    link_sources_to_concepts()
    print("✅ Auto-linking complete")
