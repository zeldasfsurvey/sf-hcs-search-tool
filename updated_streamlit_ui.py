import streamlit as st
import pandas as pd
import os
import json

# Import our new backend helpers
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
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        st.error("Manifest not found. Please run 'python -m backend.build_manifest' first.")
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
                            st.markdown(f"**{result['doc_title']}**")
                            st.markdown(f"*{result['section_label']}* (Page {result['page']})")
                            
                        with col_button:
                            url = viewer_url(result['doc_file'], result['page'])
                            st.link_button("📖 Open Section", url, use_container_width=True)
                        
                        if i < len(results) - 1:
                            st.divider()
            else:
                st.info("No matching sections found. Try different keywords or browse by style + year.")
    
    with col2:
        st.subheader("🎯 Quick Style + Year Lookup")
        
        if not frameworks_df.empty:
            # Style selection
            available_styles = sorted(frameworks_df['style'].unique())
            style = st.selectbox("Select architectural style:", [""] + available_styles)
            
            # Year input
            year = st.number_input("Year built:", min_value=1800, max_value=2024, value=1900)
            
            if style:
                dest = resolve_style_year(manifest, frameworks_df, style, year)
                
                if dest:
                    st.success(f"Found: **{dest['style']}** ({dest['period']})")
                    st.write(f"📄 Document: *{dest['doc_file'].replace('.pdf', '')}*")
                    st.write(f"📍 Section: *{dest['section_label']}*")
                    
                    # Big open button
                    url = viewer_url(dest['doc_file'], dest['page'])
                    st.link_button(
                        f"🚀 Open {dest['style']} Evaluation Criteria (p.{dest['page']})",
                        url,
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    st.warning(f"No evaluation criteria found for **{style}** in {year}. Try searching by keywords instead.")
        else:
            st.info("Framework mapping not loaded. Please ensure `data/config/frameworks_template.csv` exists.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Quick Tips:** "
        "• Search for exact style names for best results "
        "• Use the Style + Year tool when you know both "
        "• All links open in PDF.js viewer with direct page navigation"
    )

if __name__ == "__main__":
    main()