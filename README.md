# SF Historic Context Statements Search Tool

A search tool for San Francisco Historic Context Statements (HCS) that allows staff to quickly find evaluation criteria and architectural style information.

## Features

- **Smart Search**: Search across all HCS documents by architectural style, theme, or keywords
- **Direct PDF Links**: Open sections directly in PDF.js viewer with page navigation
- **Fast Results**: Pre-parsed tool 1,000+ sections across 13 documents

## Available Styles

### Early Settlement Era (1848-1906)
- Greek Revival
- Folk Victorian  
- Gothic Revival
- Early Vernacular

### Victorian Era
- Italianate
- Second Empire
- Stick/Eastlake
- Queen Anne

### Modernistic Styles (1925-1965)
- Art Deco
- Streamline Moderne
- International Style

### Modern & Postmodern
- Late Modernism
- Brutalism
- Postmodernism
- New Formalism
- Third Bay Tradition


## Usage

### Search by Keywords
- Type exact style names: "Art Deco", "Streamline Moderne"
- Use variations: "Gothic", "Victorian", "Modern"
- Search themes: "Evaluation Criteria", "Historic Context"

### Search Tips
- **Exact matches work best**: "Art Deco" vs "art deco"
- **Try different variations**: "Gothic Revival" or just "Gothic"
- **Use specific terms**: "Italianate", "Queen Anne", "Second Empire"
- **Search for sections**: "Evaluation Criteria", "Theme"

## Project Structure

```
Search Tool/
├── backend/                 # Core functionality
│   ├── build_manifest.py   # PDF parsing and indexing
│   ├── fetch_pdfs.py       # Download PDFs from GitHub
│   ├── sections.py         # Search functionality
│   └── links.py           # PDF viewer URL generation
├── ui/                     # Streamlit interface
│   └── app.py             # Main application
├── data/                   # Data storage
│   ├── config/            # Configuration files
│   ├── pdfs/              # Downloaded PDF files
│   └── metadata/          # Generated search index
└── requirements.txt        # Python dependencies
```

## Data Sources

PDF files are sourced from the [sfsurvey-hcs-pdfs](https://github.com/zeldasfsurvey/sfsurvey-hcs-pdfs) repository, which contains:

- **Early Settlement Era Styles (1848-1906)_Adopted_2025.pdf**
- **Victorian Era Historic Context Statement.pdf**
- **Modernistic Styles Historic Context Statement.pdf**
- **Modern & PostModern Styles HCS_Adopted_2024.pdf**
- **For Website - Progressive Era.pdf**
- **Biographical files (Bios_*.pdf)**

## Development

### Adding New Styles
1. Update `data/config/frameworks_template.csv` with new style mappings
2. Rebuild manifest: `python backend/build_manifest.py`
3. Test search functionality

### Customizing Search
- Modify `LABEL_PATTERNS` in `backend/build_manifest.py` to capture different section types
- Update search logic in `backend/sections.py` for different matching strategies

## Contributing
For questions or contributions, please contact the SF Survey team.
