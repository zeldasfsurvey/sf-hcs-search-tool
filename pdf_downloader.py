import os, requests
from backend.links import RAW_PREFIX

PDF_DIR = "data/pdfs"
PDF_LIST_FILE = "data/config/pdf_list.txt"

def download_pdf(url: str, filename: str):
    """Download a single PDF from URL to local directory."""
    local_path = os.path.join(PDF_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(local_path):
        print(f"  {filename} already exists, skipping")
        return True
    
    try:
        print(f"  Downloading {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        print(f"  ✓ Downloaded {filename} ({total_size} bytes)")
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to download {filename}: {e}")
        return False

def fetch_all_pdfs():
    """Download all PDFs listed in pdf_list.txt from GitHub."""
    os.makedirs(PDF_DIR, exist_ok=True)
    
    if not os.path.exists(PDF_LIST_FILE):
        # Create a template list with your known PDFs
        print(f"Creating template {PDF_LIST_FILE}...")
        os.makedirs(os.path.dirname(PDF_LIST_FILE), exist_ok=True)
        
        # You'll need to replace this with your actual PDF filenames
        template_pdfs = [
            "Early Settlement Era Styles (1848-1906)_Adopted_2025.pdf",
            "Victorian Era Historic Context Statement.pdf", 
            "Modernistic Styles Historic Context Statement.pdf",
            # Add your other PDF filenames here
        ]
        
        with open(PDF_LIST_FILE, 'w') as f:
            for pdf in template_pdfs:
                f.write(f"{RAW_PREFIX}{pdf}\n")
        
        print(f"Please edit {PDF_LIST_FILE} and add all your PDF raw URLs, then run this script again.")
        return
    
    print(f"Reading PDF list from {PDF_LIST_FILE}...")
    
    with open(PDF_LIST_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(urls)} PDFs to download:")
    
    success_count = 0
    for url in urls:
        filename = url.split('/')[-1]
        if download_pdf(url, filename):
            success_count += 1
    
    print(f"\nDownload complete: {success_count}/{len(urls)} successful")

if __name__ == "__main__":
    fetch_all_pdfs()