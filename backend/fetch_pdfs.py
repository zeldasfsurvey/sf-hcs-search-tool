"""
PDF fetching module for SF Historic Context Statements search tool.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_downloader import fetch_all_pdfs

# Re-export the main function
__all__ = ['fetch_all_pdfs']
