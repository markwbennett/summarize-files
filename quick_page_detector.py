#!/usr/bin/env python3
"""
Quick detector for problematic PDF page characteristics without hanging.
"""

import pdfplumber
from pathlib import Path
import sys

def detect_problematic_page_characteristics(pdf_path: Path, page_num: int):
    """Quickly detect characteristics that might cause PyPDF2 to hang."""
    print(f"🔍 Quick analysis of page {page_num + 1}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                print(f"❌ Page {page_num + 1} out of range")
                return None
            
            page = pdf.pages[page_num]
            
            # Extract text safely
            text = page.extract_text() or ""
            
            # Analyze characteristics
            characteristics = {
                "page_number": page_num + 1,
                "text_length": len(text),
                "has_tables": len(page.find_tables()) > 0,
                "table_count": len(page.find_tables()),
                "has_images": len(page.images) > 0 if hasattr(page, 'images') else False,
                "image_count": len(page.images) if hasattr(page, 'images') else 0,
                "page_width": page.width,
                "page_height": page.height,
                "is_table_of_contents": "contents" in text.lower() or "table of contents" in text.lower(),
                "has_complex_layout": False,
                "text_sample": text[:200] + "..." if len(text) > 200 else text
            }
            
            # Detect complex layouts
            tables = page.find_tables()
            if len(tables) > 0:
                # Check for complex table structures
                for table in tables:
                    if hasattr(table, 'cells') and len(table.cells) > 50:
                        characteristics["has_complex_layout"] = True
                        break
            
            # Print findings
            print(f"  📄 Page size: {page.width:.1f} x {page.height:.1f}")
            print(f"  📝 Text length: {len(text)} characters")
            print(f"  📊 Tables: {len(tables)}")
            print(f"  🖼️  Images: {characteristics['image_count']}")
            print(f"  📋 Is TOC: {characteristics['is_table_of_contents']}")
            print(f"  🔧 Complex layout: {characteristics['has_complex_layout']}")
            
            if text:
                print(f"  📖 Text sample: {text[:100]}...")
            
            return characteristics
            
    except Exception as e:
        print(f"❌ Error analyzing page: {e}")
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python quick_page_detector.py <pdf_path> <page_number>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    page_number = int(sys.argv[2]) - 1
    
    result = detect_problematic_page_characteristics(pdf_path, page_number)
    
    if result:
        print("\n🎯 Problematic characteristics detected:")
        if result["is_table_of_contents"]:
            print("  - Table of Contents page")
        if result["has_tables"] and result["table_count"] > 2:
            print(f"  - Multiple tables ({result['table_count']})")
        if result["has_complex_layout"]:
            print("  - Complex table layout")
        if result["text_length"] < 100:
            print("  - Very sparse text content")

if __name__ == "__main__":
    main() 