import os, re, json, glob, fitz

PDF_DIR = "data/pdfs"                  # where local PDFs live (for parsing)
OUT_PATH = "data/metadata/manifest.json"

# Label patterns we care about (add more as needed)
LABEL_PATTERNS = [
    r"Evaluation Criteria:\s*.+",
    r"Evaluative Framework[s]?:\s*.+", 
    r"Theme:\s*.+",
    r"Sub[- ]Theme:\s*.+",
    r"Style:\s*.+",
]

def parse_toc_lines(text: str):
    """
    Parse ToC-like lines, e.g.:
      'Evaluation Criteria: Gothic Revival .......... 30'
      'Sub-Theme: Art Deco ................................ 18'
    Return list of (label, page).
    """
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        # match "... 30" or " 30" at end; allow dots or spaces
        m = re.search(r"(.+?)(?:\s+\.{3,}\s+|\s+)\b(\d{1,4})\b\s*$", line)
        if not m: 
            continue
        label = m.group(1).strip()
        page = int(m.group(2))
        # ignore junk like "Table of Contents"
        if page == 0 or len(label) < 4:
            continue
        out.append((label, page))
    return out

def scan_headings(page_num: int, text: str):
    """Fallback: scan a page's text for heading-like labels."""
    hits = []
    for pat in LABEL_PATTERNS:
        for m in re.finditer(pat, text, flags=re.I):
            label = m.group(0).strip()
            hits.append((label, page_num))
    return hits

def build_manifest():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    manifest = {}
    
    for pdf_path in glob.glob(os.path.join(PDF_DIR, "*.pdf")):
        print(f"Processing {os.path.basename(pdf_path)}...")
        doc = fitz.open(pdf_path)
        fname = os.path.basename(pdf_path)
        sections = []

        # 1) Try ToC on first few pages
        toc_hits = []
        for p in range(min(7, len(doc))):
            text = doc[p].get_text("text") or ""
            toc_hits.extend(parse_toc_lines(text))

        if toc_hits:
            # de-dup + sort by page
            seen = set()
            for label, start in sorted(toc_hits, key=lambda x: x[1]):
                key = (label.lower(), start)
                if key in seen:
                    continue
                seen.add(key)
                sections.append({"label": label, "start": int(start)})
            print(f"  Found {len(sections)} sections from ToC")

        # 2) Fallback: scan headings across all pages
        if not sections:
            print(f"  No ToC found, scanning all pages...")
            seen = set()
            for p in range(len(doc)):
                text = doc[p].get_text("text") or ""
                for (label, start) in scan_headings(p + 1, text):
                    key = (label.lower(), start)
                    if key in seen:
                        continue
                    seen.add(key)
                    sections.append({"label": label, "start": int(start)})
            print(f"  Found {len(sections)} sections from heading scan")

        if sections:
            manifest[fname] = {
                "title": os.path.splitext(fname)[0],
                "sections": sorted(sections, key=lambda s: s["start"])
            }
        
        doc.close()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\nWrote {OUT_PATH} with {len(manifest)} documents")
    for fname, data in manifest.items():
        print(f"  {fname}: {len(data['sections'])} sections")

if __name__ == "__main__":
    build_manifest()