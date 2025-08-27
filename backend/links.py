import urllib.parse

# Your GitHub repo raw URLs
RAW_PREFIX = "https://raw.githubusercontent.com/zeldasfsurvey/sfsurvey-hcs-pdfs/main/"
PDFJS = "https://mozilla.github.io/pdf.js/web/viewer.html?file="

def raw_url(doc_file: str) -> str:
    return RAW_PREFIX + doc_file

def viewer_url(doc_file: str, page: int = 1) -> str:
    raw = raw_url(doc_file)
    enc = urllib.parse.quote(raw, safe="")
    return f"{PDFJS}{enc}#page={page}"

# Test function - you can delete this later
if __name__ == "__main__":
    # Test with one of your PDFs
    test_url = viewer_url("Early Settlement Era Styles (1848-1906)_Adopted_2025.pdf", 30)
    print("Test URL:", test_url)
