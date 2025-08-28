import streamlit as st
import pandas as pd
import os
import json
import sys
from pathlib import Path

# Import our new backend helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.links import viewer_url
from backend.sections import load_manifest, find_page_of_label, nearest_section_for_page, search_all_sections

# Set up page
st.set_page_config(
    page_title="SF Historic Context Statements - Staff Tool",
    page_icon="🏛️",
    layout="wide"
)

# Load data
@st.cache_data(ttl=60)  # Cache for 1 minute to force refresh
def load_data():
    """Load manifest and frameworks data."""
    # Try to load existing manifest first
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        # Only try to build if we're not in a deployed environment
        if os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD'):
            st.error("""
            🚨 **Deployment Issue**: Search index not found.
            
            **To fix this:**
            1. Run `python -m backend.build_manifest` locally
            2. Commit `data/metadata/manifest.json` to your repo  
            3. Push to GitHub and redeploy
            """)
            return None, None
        
        # Try to build it (localhost only)
        with st.spinner("Setting up search index for first time use... This may take a few minutes."):
            try:
                # Import the build functions
                from backend.fetch_pdfs import fetch_all_pdfs
                from backend.build_manifest import build_manifest
                
                # Create directories
                os.makedirs("data/pdfs", exist_ok=True)
                os.makedirs("data/metadata", exist_ok=True)
                os.makedirs("data/config", exist_ok=True)
                
                # Download PDFs first
                st.info("📥 Downloading PDF files...")
                fetch_all_pdfs()
                
                # Build the manifest
                st.info("🔨 Building search index...")
                build_manifest()
                
                # Try loading again
                manifest = load_manifest()
                st.success("✅ Setup complete!")
                
            except Exception as e:
                st.error(f"❌ Setup failed: {e}")
                st.info("💡 Try running `python -m backend.build_manifest` locally and committing the result.")
                return None, None
    
    # Load frameworks CSV
    frameworks_csv = "data/config/frameworks_template.csv"
    if os.path.exists(frameworks_csv):
        frameworks_df = pd.read_csv(frameworks_csv)
    else:
        # Create a minimal frameworks dataframe for demo
        frameworks_df = pd.DataFrame({
            'style': ['Gothic Revival', 'Art Deco', 'Streamline Moderne', 'Queen Anne', 'Italianate'],
            'period_label': ['1848–1906', '1925–c.1936', '1935–1950', 'c.1880–1910', 'c.1860–1885'],
            'year_start': [1848, 1925, 1935, 1880, 1860],
            'year_end': [1906, 1936, 1950, 1910, 1885],
            'doc_file': ['Early Settlement Era Styles (1848-1906)_Adopted_2025.pdf'] * 5,
            'section_label': ['Evaluation Criteria: Gothic Revival'] * 5
        })
    
    return manifest, frameworks_df

def resolve_style_year(manifest, frameworks_df, style: str, year: int):
    """Resolve Style + Year to specific document section."""
    if frameworks_df.empty or not style:
        return None
    
    # Find matching styles
    f = frameworks_df[frameworks_df["style"].str.contains(style, case=False, na=False)].copy()
    
    # Filter by year range
    try:
        f = f[(f["year_start"].astype(int) <= int(year)) & (f["year_end"].astype(int) >= int(year))]
    except Exception:
        pass
    
    if f.empty:
        return None
    
    # Get first match
    row = f.iloc[0].to_dict()
    doc_file = row.get("doc_file")
    section_label = row.get("section_label")
    
    if not (doc_file and section_label):
        return None
    
    # Find the actual page
    page = find_page_of_label(manifest, doc_file, section_label)
    if not page:
        # Fallback to page 1 if we can't find the specific section
        page = 1
    
    return {
        "doc_file": doc_file, 
        "section_label": section_label, 
        "page": int(page),
        "style": row.get("style"),
        "period": row.get("period_label")
    }

# Main app
def main():
    st.title("🏛️ SF Survey Historic Context Statements")
    st.markdown("*Search tool for staff evaluation*")
    
    # Load data
    manifest, frameworks_df = load_data()
    if manifest is None:
        st.stop()
    
    # Check if manifest has the right content
    early_doc = 'Early%20Settlement%20Era%20Styles%20(1848-1906)_Adopted_2025.pdf'
    if early_doc in manifest:
        sections = manifest[early_doc]['sections']
        greek_sections = [s for s in sections if 'greek' in s['label'].lower()]
        if len(greek_sections) == 0:
            st.error("⚠️ Manifest appears to be outdated. Please redeploy the app.")
            st.stop()
    

    
    # Show stats
    total_sections = sum(len(doc.get('sections', [])) for doc in manifest.values())
    
    st.subheader("🔍 Search by Style or Keywords")
    
    # Search input
    query = st.text_input(
        "Search for architectural styles, themes, or evaluation criteria:",
        placeholder="e.g., Greek Revival, Art Deco, Streamline Moderne..."
    )
    
    if query:
        # Search across all sections with improved logic
        results = search_all_sections(manifest, query)
        

        
        if results:
            st.write(f"Found **{len(results)}** relevant sections:")
            
            # Show results as cards with open buttons
            for i, result in enumerate(results[:15]):  # Show more results
                with st.container():
                    col_text, col_button = st.columns([3, 1])
                    
                    with col_text:
                        # Clean up the document title for display
                        doc_title = result['doc_title']
                        doc_title = doc_title.replace('%20', ' ').replace('%26', '&').replace('%2D', '-')
                        
                        # Add visual indicator for high-relevance results
                        if result['score'] >= 8.0:
                            st.markdown(f"**{doc_title}** 🎯")
                        else:
                            st.markdown(f"**{doc_title}**")
                        
                        # Clean up the section label for display
                        section_label = result['section_label']
                        # Take only the first line and clean it up
                        clean_label = section_label.split('\n')[0].strip()
                        # Remove extra whitespace
                        clean_label = ' '.join(clean_label.split())
                        st.markdown(f"*{clean_label}* (Page {result['page']})")
                    
                    with col_button:
                        # Skip bio documents for now since they have broken links
                        if 'Bios_' in result['doc_file']:
                            st.write("🔗 PDF link unavailable")
                        else:
                            url = viewer_url(result['doc_file'], result['page'])
                            st.link_button("📖 Open Section", url, use_container_width=True)
                    
                    if i < len(results) - 1:
                        st.divider()
        else:
            st.info("No matching sections found. Try different keywords or browse the document list below.")
            
            # Show all available sections as fallback
            st.subheader("📚 All Available Sections")
            for doc_file, doc_data in list(manifest.items())[:3]:  # Show first 3 docs
                with st.expander(f"📄 {doc_data['title']}"):
                    for section in doc_data.get('sections', [])[:10]:  # Show first 10 sections
                        col_text, col_btn = st.columns([4, 1])
                        with col_text:
                            st.write(f"• {section['label']} (p.{section['start']})")
                        with col_btn:
                            url = viewer_url(doc_file, section['start'])
                            st.link_button("Open", url)
    
    # Status section at bottom
    st.markdown("---")
    st.markdown("**📊 Current Status:**")
    st.info(f"✅ **{len(manifest)} documents** loaded")
    st.info(f"✅ **{total_sections} sections** indexed")
    
    if not frameworks_df.empty:
        st.info(f"✅ **{len(frameworks_df)} styles** configured")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Quick Tips:** "
        "• Search for exact style names for best results "
        "• Try different variations of style names "
        "• All links open in PDF.js viewer with direct page navigation"
    )

if __name__ == "__main__":
    main()