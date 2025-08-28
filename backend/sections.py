import json

MANIFEST_PATH = "data/metadata/manifest.json"

def load_manifest():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def nearest_section_for_page(manifest, doc_file: str, page: int):
    """Find the section that contains this page (or the nearest one before it)."""
    d = manifest.get(doc_file)
    if not d:
        return None
    secs = d.get("sections", [])
    best = None
    for s in secs:
        if s["start"] <= page:
            if best is None or s["start"] > best["start"]:
                best = s
    return best

def find_page_of_label(manifest, doc_file: str, label_substring: str):
    """Find the page number of a section that matches the label substring."""
    d = manifest.get(doc_file)
    if not d:
        return None
    for s in d.get("sections", []):
        if label_substring.lower() in s["label"].lower():
            return int(s["start"])
    return None

def search_all_sections(manifest, query: str):
    """Search across all documents for sections matching the query."""
    results = []
    query_lower = query.lower().strip()
    
    # Define style patterns for better matching
    style_patterns = {
        'greek': 'greek revival',
        'gothic': 'gothic revival', 
        'art deco': 'art deco',
        'streamline': 'streamline moderne',
        'international': 'international style',
        'queen anne': 'queen anne',
        'italianate': 'italianate',
        'second empire': 'second empire',
        'stick': 'stick/eastlake',
        'eastlake': 'stick/eastlake',
        'folk victorian': 'folk victorian',
        'neoclassical': 'neoclassical',
        'colonial': 'colonial revival',
        'tudor': 'tudor revival',
        'spanish': 'spanish colonial revival',
        'mission': 'mission revival',
        'craftsman': 'craftsman',
        'bungalow': 'bungalow',
        'prairie': 'prairie school',
        'art moderne': 'art moderne',
        'moderne': 'art moderne',
        'bauhaus': 'bauhaus',
        'mid century': 'mid-century modern',
        'mid-century': 'mid-century modern',
        'brutalist': 'brutalist',
        'new formalism': 'new formalism',
        'postmodern': 'postmodern'
    }
    
    # Common architect names for better matching
    architect_names = {
        'anderson': 'Anderson',
        'christian': 'Christian',
        'christian anderson': 'Christian Anderson',
        'anderson christian': 'Christian Anderson',
        'denck': 'Denck',
        'edmund': 'Edmund',
        'edmund denck': 'Edmund Denck',
        'denck edmund': 'Edmund Denck',
        'august': 'August',
        'august denck': 'August Denck',
        'denck august': 'August Denck',
        'daniels': 'Daniels',
        'dillman': 'Dillman',
        'daniels dillman': 'Daniels & Dillman',
        'dillman daniels': 'Daniels & Dillman',
        'osmont': 'Osmont',
        'daniels osmont': 'Daniels & Osmont',
        'osmont daniels': 'Daniels & Osmont',
        'wilhelm': 'Wilhelm',
        'daniels wilhelm': 'Daniels & Wilhelm',
        'wilhelm daniels': 'Daniels & Wilhelm',
        'mclaren': 'McLaren',
        'donald': 'Donald',
        'donald mclaren': 'Donald McLaren',
        'mclaren donald': 'Donald McLaren',
        'mc dougall': 'McDougall',
        'mcdougall': 'McDougall',
        'barnett': 'Barnett',
        'barnett mc dougall': 'Barnett McDougall',
        'mc dougall barnett': 'Barnett McDougall',
        'marquis': 'Marquis',
        'mc dougall marquis': 'McDougall & Marquis',
        'marquis mc dougall': 'McDougall & Marquis',
        'mclaren': 'McDougall',  # Common misspelling
        'donald mclaren': 'Donald McDougall'
    }
    
    # Check if query matches a style pattern or architect name
    expanded_query = query_lower
    for pattern, full_style in style_patterns.items():
        if pattern in query_lower:
            expanded_query = full_style
            break
    
    # Check if query matches an architect name
    for pattern, full_name in architect_names.items():
        if pattern in query_lower:
            expanded_query = full_name
            break
    
    for doc_file, data in manifest.items():
        for section in data.get("sections", []):
            section_label_lower = section["label"].lower()
            
            # Calculate relevance score
            score = 0.0
            
            # Get the first line of the section label (cleaner)
            first_line = section_label_lower.split('\n')[0].strip()
            
            # Exact match gets highest score
            if query_lower == first_line:
                score = 10.0
            # Full style name match in first line
            elif expanded_query in first_line:
                score = 8.0
            # Partial match in first line
            elif query_lower in first_line:
                score = 5.0
            # Style pattern match in first line
            elif any(pattern in first_line for pattern in style_patterns.keys() if pattern in query_lower):
                score = 3.0
            # Architect name pattern match (handle "Last, First" format)
            elif any(name.lower() in first_line for name in architect_names.values() if name.lower() in query_lower):
                score = 4.0
            # Individual name part match (for searching just first or last name)
            elif any(part in first_line for part in query_lower.split() if len(part) > 2):
                score = 2.0
            
            # Boost evaluation criteria sections
            if 'evaluation criteria' in first_line:
                score += 2.0
            
            # Boost architect name matches in biographical documents
            if 'bios_' in doc_file.lower() and any(name in first_line for name in architect_names.values()):
                score += 1.5
            
            # Penalize very long/messy labels
            if len(section_label_lower) > 200:
                score -= 1.0
            
            # Only include results with meaningful matches
            if score > 0:
                # Filter out very low relevance results for better user experience
                if score >= 3.0:  # Lowered threshold to catch more results
                    results.append({
                        "doc_file": doc_file,
                        "doc_title": data["title"],
                        "section_label": section["label"],
                        "page": section["start"],
                        "score": score
                    })
    
    # Sort by relevance score (highest first)
    return sorted(results, key=lambda x: (-x["score"], x["page"]))

# Test function
if __name__ == "__main__":
    try:
        manifest = load_manifest()
        print("Manifest loaded successfully!")
        print(f"Found {len(manifest)} documents")
        
        # Test search
        results = search_all_sections(manifest, "Gothic Revival")
        print(f"\nSearch for 'Gothic Revival' found {len(results)} results:")
        for r in results:
            print(f"  {r['doc_title']} - {r['section_label']} (p.{r['page']})")
            
    except FileNotFoundError:
        print("Manifest not found. Run 'python -m backend.build_manifest' first.")
