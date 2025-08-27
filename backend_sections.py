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
    query_lower = query.lower()
    
    for doc_file, data in manifest.items():
        for section in data.get("sections", []):
            if query_lower in section["label"].lower():
                results.append({
                    "doc_file": doc_file,
                    "doc_title": data["title"],
                    "section_label": section["label"],
                    "page": section["start"],
                    "score": 1.0 if query_lower == section["label"].lower() else 0.8
                })
    
    # Sort by relevance (exact matches first)
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