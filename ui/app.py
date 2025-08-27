import streamlit as st
import pandas as pd
import os
import json

# Import our new backend helpers
import sys
import os
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
@st.cache_data
def load_data():
    """Load manifest and frameworks data."""
    # Check if we need to download PDFs and build manifest
    if not os.path.exists("data/metadata/manifest.json"):
        with st.spinner("Setting up search index... This may take a few minutes on first run."):
            try:
                # Import and run the setup functions
                from backend.fetch_pdfs import fetch_all_pdfs
                from backend.build_manifest import build_manifest
                
                # Download PDFs
                st.info("Downloading PDF files...")
                fetch_all_pdfs()
                
                # Build manifest
                st.info("Building search index...")
                build_manifest()
                
                st.success("Setup complete!")
            except Exception as e:
                st.error(f"Setup failed: {e}")
                return None, None
    
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        st.error("Manifest not found. Please try refreshing the page.")
        return None, None
    
    frameworks_csv = "data/config/frameworks_template.csv"
    if os.path.exists(frameworks_csv):
        frameworks_df = pd.read_csv(frameworks_csv)
    else:
        frameworks_df = pd.DataFrame()
    
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
        return None
    
    return {
        "doc_file": doc_file, 
        "section_label": section_label, 
        "page": int(page),
        "style": row.get("style"),
        "period": row.get("period_label")
    }

# Main app
def main():
    st.title("🏛️ SF Historic Context Statements")
    st.markdown("*Staff evaluation tool for architectural styles and historic contexts*")
    
    # Load data
    manifest, frameworks_df = load_data()
    if manifest is None:
        st.info("Please wait while the app sets up... If this takes too long, try refreshing the page.")
        return
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Search by Style or Keywords")
        
        # Search input
        query = st.text_input(
            "Search for architectural styles, themes, or evaluation criteria:",
            placeholder="e.g., Gothic Revival, Art Deco, Streamline Moderne..."
        )
        
        if query:
            # Search across all sections
            results = search_all_sections(manifest, query)
            
            if results:
                st.write(f"Found **{len(results)}** relevant sections:")
                
                # Show results as cards with open buttons
                for i, result in enumerate(results[:10]):  # Limit to top 10
                    with st.container():
                        col_text, col_button = st.columns([3, 1])
                        
                        with col_text:
                            # Clean up the document title for display
                            doc_title = result['doc_title']
                            doc_title = doc_title.replace('%20', ' ').replace('%26', '&')
                            st.markdown(f"**{doc_title}**")
                            st.markdown(f"*{result['section_label']}* (Page {result['page']})")
                            
                        with col_button:
                            url = viewer_url(result['doc_file'], result['page'])
                            st.link_button("📖 Open Section", url, use_container_width=True)
                        
                        if i < len(results) - 1:
                            st.divider()
            else:
                st.info("No matching sections found. Try different keywords or browse by style + year.")
    
    with col2:
        st.subheader("💡 Search Tips")
        
        st.markdown("""
        **How to search effectively:**
        
        • **Exact style names work best**: "Art Deco", "Streamline Moderne"
        • **Try variations**: "Gothic", "Victorian", "Modern"
        • **Search for themes**: "Evaluation Criteria", "Historic Context"
        • **Use specific terms**: "Italianate", "Queen Anne", "Second Empire"
        
        **Available styles include:**
        • **Early Settlement**: Greek Revival, Folk Victorian, Gothic Revival
        • **Victorian Era**: Italianate, Second Empire, Stick/Eastlake, Queen Anne  
        • **Modernistic**: Art Deco, Streamline Moderne, International Style
        • **Modern & Postmodern**: Late Modernism, Brutalism, Postmodernism, New Formalism
        
        **Search results show actual section headers from table of contents!**
        """)
        
        st.markdown("---")
        st.markdown("**📊 Current Status:**")
        st.info(f"✅ **{len(manifest)} documents** loaded with **{sum(len(doc.get('sections', [])) for doc in manifest.values())} sections**")
        
        if not frameworks_df.empty:
            st.success(f"✅ **{len(frameworks_df)} styles** configured for direct lookup")
        else:
            st.warning("⚠️ Framework mapping not loaded")
    
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