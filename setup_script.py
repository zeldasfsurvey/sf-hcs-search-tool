#!/usr/bin/env python3
"""
Setup script for SF Historic Context Statements search tool.
Run this to set up directories, download PDFs, and build the manifest.
"""

import os
import subprocess
import sys

def create_directories():
    """Create necessary directories."""
    dirs = [
        "data/pdfs",
        "data/metadata", 
        "data/config",
        "backend"
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✓ Created directory: {d}")

def check_python_packages():
    """Check if required packages are installed."""
    required = ["fitz", "requests", "pandas", "streamlit"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✓ {pkg} is installed")
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} is missing")
    
    if missing:
        print(f"\nPlease install missing packages:")
        print(f"pip install {' '.join(missing)}")
        print("Or run: pip install -r requirements.txt")
        return False
    return True

def run_pdf_download():
    """Download PDFs from GitHub."""
    print("\n🔽 Downloading PDFs from GitHub...")
    try:
        from backend.fetch_pdfs import fetch_all_pdfs
        fetch_all_pdfs()
        return True
    except Exception as e:
        print(f"Error downloading PDFs: {e}")
        return False

def build_manifest():
    """Build the sections manifest from PDFs."""
    print("\n📋 Building sections manifest...")
    try:
        from backend.build_manifest import build_manifest as build
        build()
        return True
    except Exception as e:
        print(f"Error building manifest: {e}")
        return False

def test_system():
    """Test that everything is working."""
    print("\n🧪 Testing system...")
    try:
        from backend.sections import load_manifest, search_all_sections
        from backend.links import viewer_url
        
        manifest = load_manifest()
        print(f"✓ Manifest loaded: {len(manifest)} documents")
        
        # Test search
        results = search_all_sections(manifest, "Gothic")
        print(f"✓ Search test: found {len(results)} results for 'Gothic'")
        
        # Test URL generation
        if results:
            first_result = results[0]
            url = viewer_url(first_result['doc_file'], first_result['page'])
            print(f"✓ URL generation test: {url[:80]}...")
        
        return True
    except Exception as e:
        print(f"✗ System test failed: {e}")
        return False

def main():
    print("🏛️ SF Historic Context Statements - Setup")
    print("=" * 50)
    
    # Step 1: Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Step 2: Check packages
    print("\n2. Checking Python packages...")
    if not check_python_packages():
        print("\n❌ Setup failed. Please install required packages first.")
        return
    
    # Step 3: Download PDFs
    print("\n3. Downloading PDFs...")
    if not run_pdf_download():
        print("\n⚠️  PDF download failed. Please check your PDF list and try again.")
        print("You may need to manually edit data/config/pdf_list.txt")
    
    # Step 4: Build manifest
    print("\n4. Building manifest...")
    if not build_manifest():
        print("\n❌ Manifest building failed. Check that PDFs are in data/pdfs/")
        return
    
    # Step 5: Test system
    print("\n5. Testing system...")
    if not test_system():
        print("\n❌ System test failed.")
        return
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Review and edit data/config/frameworks_template.csv")
    print("2. Run the app: streamlit run ui/app.py")
    print("3. Test search functionality")

if __name__ == "__main__":
    main()