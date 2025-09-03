import os, re, json, glob, fitz
import sys
from pathlib import Path

PDF_DIR = "data/pdfs"                  # where local PDFs live (for parsing)
OUT_PATH = "data/metadata/manifest.json"

# Expanded label patterns for SF Historic Context Statements
LABEL_PATTERNS = [
    # Primary evaluation patterns
    r"Evaluation Criteria:\s*.+",
    r"Evaluative Framework[s]?:\s*.+",
    r"Evaluative Criteria:\s*.+",
    
    # Style and theme patterns
    r"Style:\s*.+",
    r"Sub[- ]?style:\s*.+",
    r"Theme:\s*.+", 
    r"Sub[- ]?Theme:\s*.+",
    r"Sub[- ]?theme:\s*.+",
    
    # Historic context patterns
    r"Historic Context:\s*.+",
    r"Historical Context:\s*.+",
    r"Context Statement:\s*.+",
    
    # Property type patterns  
    r"Property Type:\s*.+",
    r"Building Type:\s*.+",
    r"Resource Type:\s*.+",
    
    # Period and era patterns
    r"Period of Significance:\s*.+",
    r"Time Period:\s*.+",
    r"Era:\s*.+",
    
    # Common architectural style names (catch standalone mentions)
    r"Gothic Revival\b",
    r"Art Deco\b", 
    r"Streamline Moderne\b",
    r"International Style\b",
    r"Queen Anne\b",
    r"Italianate\b",
    r"Second Empire\b",
    r"Stick[/\\]?Eastlake\b",
    r"Folk Victorian\b",
    r"Greek Revival\b",
    r"Neoclassical\b",
    r"Colonial Revival\b",
    r"Tudor Revival\b",
    r"Spanish Colonial Revival\b",
    r"Mission Revival\b",
    r"Craftsman\b",
    r"Bungalow\b",
    r"Prairie School\b",
    r"Art Moderne\b",
    r"Moderne\b",
    r"Bauhaus\b",
    r"Mid[- ]?Century Modern\b",
    r"Brutalist\b",
    r"New Formalism\b",
    r"Postmodern\b",
]

def parse_toc_lines(text: str):
    """
    Parse ToC-like lines, e.g.:
      'Evaluation Criteria: Gothic Revival .......... 30'
      'Sub-Theme: Art Deco ................................ 18' 
      'Gothic Revival 25'
      'Theme: Residential Architecture    12'
    Return list of (label, page).
    """
    out = []
    lines = text.splitlines()
    
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
            
        # Pattern 1: "Label ........ 30" or "Label     30"
        m = re.search(r"(.+?)(?:\s+\.{2,}\s*|\s{3,})\b(\d{1,4})\b\s*$", line)
        if m:
            label = m.group(1).strip()
            page = int(m.group(2))
        else:
            # Pattern 2: "Label 30" (simple space separation)
            m = re.search(r"(.+?)\s+(\d{1,4})\s*$", line)
            if m:
                label = m.group(1).strip()
                page = int(m.group(2))
            else:
                # Pattern 3: Check if next line is a page number
                if i + 1 < len(lines) and re.match(r"^\d+$", lines[i + 1].strip()):
                    label = line
                    page = int(lines[i + 1].strip())
                else:
                    continue
        
        # Clean up label
        label = re.sub(r'\s+', ' ', label)  # normalize whitespace
        label = label.replace('..', '').replace('…', '').strip()  # remove dots
        
        # Skip obviously wrong entries
        if (page == 0 or len(label) < 3 or 
            'table of contents' in label.lower() or
            'contents' == label.lower() or
            label.lower().startswith('page ') or
            re.match(r'^\d+$', label.strip())):  # just numbers
            continue
            
        # Skip very generic entries unless they have specific keywords
        generic_terms = ['introduction', 'overview', 'summary', 'conclusion', 'appendix']
        if any(term in label.lower() for term in generic_terms):
            # Only include if it has specific architectural/historic terms
            if not any(term in label.lower() for term in ['style', 'criteria', 'context', 'theme', 'evaluation', 'greek', 'gothic', 'victorian']):
                continue
        
        out.append((label, page))
    return out

def scan_headings(page_num: int, text: str):
    """Fallback: scan a page's text for heading-like labels."""
    hits = []
    for pat in LABEL_PATTERNS:
        for m in re.finditer(pat, text, flags=re.I):
            label = m.group(0).strip()
            # Clean up the label
            label = re.sub(r'\s+', ' ', label)
            # Skip very short matches unless they're exact style names
            if len(label) < 8 and not any(style in label for style in ['Art Deco', 'Moderne', 'Bauhaus']):
                continue
            hits.append((label, page_num))
    return hits

def extract_pdf_text_safely(doc, page_num):
    """Safely extract text from a PDF page with error handling."""
    try:
        page = doc[page_num]
        return page.get_text("text") or ""
    except Exception as e:
        print(f"    Warning: Could not read page {page_num + 1}: {e}")
        return ""

def find_toc_pages(doc, max_pages=10):
    """Try to identify which pages contain table of contents."""
    toc_pages = []
    
    for p in range(min(max_pages, len(doc))):
        text = extract_pdf_text_safely(doc, p)
        if not text:
            continue
            
        text_lower = text.lower()
        # Look for ToC indicators
        toc_indicators = [
            'table of contents', 'contents', 'index',
            'evaluation criteria:', 'theme:', 'style:',
            'page', 'chapter'
        ]
        
        # Count dots (common in ToC formatting)
        dot_count = text.count('.')
        
        if (any(indicator in text_lower for indicator in toc_indicators) or 
            dot_count > 20):  # Lots of dots usually means ToC
            toc_pages.append(p)
    
    return toc_pages if toc_pages else list(range(min(7, len(doc))))

def is_bio_document(filename):
    """Check if this is a biographical document."""
    return 'bios_' in filename.lower()

def parse_bio_document(doc):
    """Parse biographical documents to find architect entries and their page numbers."""
    bio_sections = []
    
    # Scan through pages to find architect names and their corresponding pages
    for page_num in range(len(doc)):
        text = extract_pdf_text_safely(doc, page_num)
        if not text:
            continue
        
        # Look for patterns like "Name, First" or "Name, First Middle"
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Pattern: "Last, First" or "Last, First Middle"
            # This matches architect names in bio documents
            if re.match(r'^[A-Z][a-z]+, [A-Z]', line):
                # Clean up the name
                name = line.split(',')[0].strip()
                if len(name) > 2:  # Avoid very short names
                    bio_sections.append({
                        "label": line,
                        "start": page_num + 1  # Convert to 1-based page numbers
                    })
            
            # Pattern: "See also: Name, Name" or "See also: Name + Name"
            # This captures cross-references to other architects/firms
            elif line.startswith('See also:') and len(line) > 10:
                # Extract the names after "See also:"
                names_part = line[10:].strip()
                if names_part and len(names_part) > 3:
                    bio_sections.append({
                        "label": line,
                        "start": page_num + 1  # Convert to 1-based page numbers
                    })
            
            # Pattern: "Name + Name" (firm names)
            # This captures firm names like "Anshen + Allen"
            elif re.search(r'[A-Z][a-z]+\s+\+\s+[A-Z][a-z]+', line):
                if len(line) > 5 and not line.startswith('See also:'):
                    bio_sections.append({
                        "label": line,
                        "start": page_num + 1  # Convert to 1-based page numbers
                    })
    
    return bio_sections

def build_manifest():
    """Build the manifest by scanning all PDFs for sections and page numbers."""
    print("🏗️  Building sections manifest...")
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Check if PDF directory has files
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {PDF_DIR}")
        print("💡 Please download PDFs first using: python backend/fetch_pdfs.py")
        return
    
    print(f"📚 Found {len(pdf_files)} PDF files to process")
    manifest = {}
    processed_count = 0
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\n📄 Processing {filename}...")
        
        try:
            doc = fitz.open(pdf_path)
            sections = []
            
            # Method 1: Try ToC extraction from likely pages
            toc_pages = find_toc_pages(doc)
            toc_hits = []
            
            print(f"    🔍 Scanning ToC on pages {[p+1 for p in toc_pages]}")
            for p in toc_pages:
                text = extract_pdf_text_safely(doc, p)
                if text:
                    page_hits = parse_toc_lines(text)
                    toc_hits.extend(page_hits)
                    if page_hits:
                        print(f"      Page {p+1}: found {len(page_hits)} entries")

            if toc_hits:
                # De-duplicate and sort by page
                seen = set()
                for label, start in sorted(toc_hits, key=lambda x: x[1]):
                    key = (label.lower().strip(), start)
                    if key in seen:
                        continue
                    seen.add(key)
                    sections.append({"label": label, "start": int(start)})
                
                print(f"    ✅ Extracted {len(sections)} sections from ToC")
            
            # Special handling for bio documents
            if is_bio_document(filename):
                print(f"    🔍 Special handling for bio document...")
                bio_sections = parse_bio_document(doc)
                if bio_sections:
                    sections = bio_sections  # Replace with bio sections
                    print(f"    ✅ Extracted {len(bio_sections)} bio sections")
                else:
                    print(f"    ⚠️ No bio sections found, using regular parsing")

            # Method 2: Fallback - scan all pages for headings
            if not sections:
                print(f"    ⚠️  No ToC found, scanning all {len(doc)} pages for headings...")
                seen = set()
                
                # Limit scanning for very large documents
                max_scan_pages = min(len(doc), 200)  # Don't scan more than 200 pages
                
                for p in range(max_scan_pages):
                    if p % 20 == 0 and p > 0:
                        print(f"      Scanned {p}/{max_scan_pages} pages...")
                        
                    text = extract_pdf_text_safely(doc, p)
                    if text:
                        for (label, start) in scan_headings(p + 1, text):
                            key = (label.lower().strip(), start)
                            if key in seen:
                                continue
                            seen.add(key)
                            sections.append({"label": label, "start": int(start)})
                
                print(f"    ✅ Found {len(sections)} sections from heading scan")

            # Add to manifest if we found sections
            if sections:
                manifest[filename] = {
                    "title": os.path.splitext(filename)[0],
                    "sections": sorted(sections, key=lambda s: s["start"]),
                    "total_pages": len(doc)
                }
                processed_count += 1
            else:
                print(f"    ⚠️  No sections found in {filename}")
            
            doc.close()
            
        except Exception as e:
            print(f"    ❌ Error processing {filename}: {e}")
            continue

    # Write the manifest
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Successfully built manifest!")
        print(f"📁 Wrote {OUT_PATH}")
        print(f"📊 Processed {processed_count}/{len(pdf_files)} documents")
        
        # Summary
        total_sections = sum(len(doc['sections']) for doc in manifest.values())
        print(f"📋 Total sections indexed: {total_sections}")
        
        print(f"\n📝 Document breakdown:")
        for filename, data in manifest.items():
            sections_count = len(data['sections'])
            print(f"  • {filename}: {sections_count} sections ({data.get('total_pages', '?')} pages)")
            
        # Show a few sample sections
        if manifest:
            print(f"\n🔍 Sample sections found:")
            sample_count = 0
            for doc_data in manifest.values():
                for section in doc_data['sections'][:3]:  # First 3 from each doc
                    if sample_count >= 10:  # Max 10 samples
                        break
                    print(f"  • {section['label']} (p.{section['start']})")
                    sample_count += 1
                if sample_count >= 10:
                    break
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to write manifest: {e}")
        return False

def validate_manifest(manifest_path=OUT_PATH):
    """Validate the built manifest for common issues."""
    print(f"\n🔍 Validating manifest...")
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"❌ Cannot read manifest: {e}")
        return False
    
    if not manifest:
        print(f"❌ Manifest is empty")
        return False
    
    issues = []
    warnings = []
    
    for filename, doc_data in manifest.items():
        # Check required fields
        if 'title' not in doc_data:
            issues.append(f"{filename}: missing 'title' field")
        if 'sections' not in doc_data:
            issues.append(f"{filename}: missing 'sections' field")
            continue
            
        sections = doc_data['sections']
        if not sections:
            warnings.append(f"{filename}: no sections found")
            continue
        
        # Check section structure
        prev_page = 0
        for i, section in enumerate(sections):
            if 'label' not in section:
                issues.append(f"{filename} section {i}: missing 'label'")
            if 'start' not in section:
                issues.append(f"{filename} section {i}: missing 'start' page")
            else:
                page = section['start']
                if page <= prev_page and prev_page != 0:
                    warnings.append(f"{filename}: section '{section.get('label', '?')}' page {page} is not after previous page {prev_page}")
                prev_page = page
        
        # Check for evaluation criteria
        eval_sections = [s for s in sections if 'evaluation criteria' in s.get('label', '').lower()]
        if not eval_sections:
            warnings.append(f"{filename}: no 'Evaluation Criteria' sections found")
    
    # Report results
    if issues:
        print(f"❌ Found {len(issues)} critical issues:")
        for issue in issues[:10]:  # Show max 10
            print(f"   • {issue}")
        return False
    
    if warnings:
        print(f"⚠️  Found {len(warnings)} warnings:")
        for warning in warnings[:10]:  # Show max 10
            print(f"   • {warning}")
    
    print(f"✅ Manifest validation complete")
    return True

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("🏛️  SF Historic Context Statements - Manifest Builder")
            print("Usage:")
            print("  python -m backend.build_manifest        # Build manifest")
            print("  python -m backend.build_manifest --validate # Validate existing manifest")
            print("  python -m backend.build_manifest --help     # Show this help")
            sys.exit(0)
        elif sys.argv[1] == '--validate':
            if os.path.exists(OUT_PATH):
                validate_manifest()
            else:
                print(f"❌ Manifest not found at {OUT_PATH}")
            sys.exit(0)
    
    # Main execution
    print("🏛️  SF Historic Context Statements - Manifest Builder")
    print("=" * 60)
    
    success = build_manifest()
    
    if success:
        # Auto-validate after building
        validate_manifest()
        print(f"\n🎯 Next steps:")
        print(f"   1. Review the manifest: cat {OUT_PATH}")
        print(f"   2. Test the search: python -m backend.sections")  
        print(f"   3. Run the app: streamlit run ui/app.py")
    else:
        print(f"\n❌ Build failed. Check the error messages above.")
        sys.exit(1)
