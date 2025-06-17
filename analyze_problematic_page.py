#!/usr/bin/env python3
"""
Analyze a specific PDF page to identify characteristics that cause PyPDF2 to hang.
"""

import PyPDF2
import pdfplumber
from pathlib import Path
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

def analyze_page_characteristics(pdf_path: Path, page_num: int):
    """Analyze characteristics of a specific page that might cause hanging."""
    print(f"🔍 Analyzing page {page_num + 1} in {pdf_path.name}")
    
    characteristics = {
        "page_number": page_num + 1,
        "file_name": pdf_path.name,
        "file_size_mb": pdf_path.stat().st_size / (1024 * 1024),
        "pypdf2_hangs": False,
        "pypdf2_error": None,
        "pypdf2_timeout": False,
        "pdfplumber_works": False,
        "pdfplumber_error": None,
        "page_content_type": None,
        "has_images": False,
        "has_tables": False,
        "has_forms": False,
        "text_length": 0,
        "extraction_time": None,
        "page_rotation": None,
        "page_size": None,
        "annotations": 0,
        "fonts": [],
        "content_streams": 0
    }
    
    # Test PyPDF2 with timeout
    print("  📖 Testing PyPDF2 extraction...")
    pypdf2_result = test_pypdf2_extraction(pdf_path, page_num)
    characteristics.update(pypdf2_result)
    
    # Test pdfplumber
    print("  📊 Testing pdfplumber extraction...")
    pdfplumber_result = test_pdfplumber_extraction(pdf_path, page_num)
    characteristics.update(pdfplumber_result)
    
    # Analyze page structure
    print("  🔍 Analyzing page structure...")
    structure_result = analyze_page_structure(pdf_path, page_num)
    characteristics.update(structure_result)
    
    return characteristics

def test_pypdf2_extraction(pdf_path: Path, page_num: int, timeout: int = 5):
    """Test PyPDF2 extraction with timeout."""
    result = {
        "pypdf2_hangs": False,
        "pypdf2_error": None,
        "pypdf2_timeout": False,
        "pypdf2_text_length": 0,
        "pypdf2_extraction_time": None
    }
    
    def extract_with_pypdf2():
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if page_num >= len(reader.pages):
                    return None, "Page number out of range"
                
                start_time = time.time()
                page = reader.pages[page_num]
                text = page.extract_text()
                end_time = time.time()
                
                return text, end_time - start_time
        except Exception as e:
            return None, str(e)
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(extract_with_pypdf2)
            text, extraction_time = future.result(timeout=timeout)
            
            if isinstance(extraction_time, str):  # It's an error message
                result["pypdf2_error"] = extraction_time
            else:
                result["pypdf2_text_length"] = len(text) if text else 0
                result["pypdf2_extraction_time"] = extraction_time
                print(f"    ✅ PyPDF2 extracted {len(text) if text else 0} chars in {extraction_time:.2f}s")
                
    except FuturesTimeoutError:
        result["pypdf2_timeout"] = True
        result["pypdf2_hangs"] = True
        print(f"    ⏰ PyPDF2 timed out after {timeout}s")
    except Exception as e:
        result["pypdf2_error"] = str(e)
        print(f"    ❌ PyPDF2 error: {e}")
    
    return result

def test_pdfplumber_extraction(pdf_path: Path, page_num: int):
    """Test pdfplumber extraction."""
    result = {
        "pdfplumber_works": False,
        "pdfplumber_error": None,
        "pdfplumber_text_length": 0,
        "pdfplumber_extraction_time": None
    }
    
    try:
        start_time = time.time()
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                result["pdfplumber_error"] = "Page number out of range"
                return result
            
            page = pdf.pages[page_num]
            text = page.extract_text()
            end_time = time.time()
            
            result["pdfplumber_works"] = True
            result["pdfplumber_text_length"] = len(text) if text else 0
            result["pdfplumber_extraction_time"] = end_time - start_time
            print(f"    ✅ pdfplumber extracted {len(text) if text else 0} chars in {end_time - start_time:.2f}s")
            
    except Exception as e:
        result["pdfplumber_error"] = str(e)
        print(f"    ❌ pdfplumber error: {e}")
    
    return result

def analyze_page_structure(pdf_path: Path, page_num: int):
    """Analyze the internal structure of the page."""
    result = {
        "page_rotation": None,
        "page_size": None,
        "annotations": 0,
        "fonts": [],
        "content_streams": 0,
        "has_images": False,
        "has_tables": False,
        "page_content_type": "unknown"
    }
    
    try:
        # Use pdfplumber for safer structure analysis
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                return result
            
            page = pdf.pages[page_num]
            
            # Basic page info
            result["page_size"] = [page.width, page.height] if hasattr(page, 'width') else None
            
            # Check for tables
            tables = page.find_tables()
            result["has_tables"] = len(tables) > 0
            if tables:
                print(f"    📊 Found {len(tables)} tables")
            
            # Check for images
            images = page.images if hasattr(page, 'images') else []
            result["has_images"] = len(images) > 0
            if images:
                print(f"    🖼️  Found {len(images)} images")
            
            # Determine content type
            text = page.extract_text() or ""
            if "contents" in text.lower() or "table of contents" in text.lower():
                result["page_content_type"] = "table_of_contents"
            elif len(tables) > 0:
                result["page_content_type"] = "table_heavy"
            elif len(images) > 0:
                result["page_content_type"] = "image_heavy"
            elif len(text.strip()) < 50:
                result["page_content_type"] = "sparse_text"
            else:
                result["page_content_type"] = "normal_text"
            
            print(f"    📋 Content type: {result['page_content_type']}")
            
    except Exception as e:
        print(f"    ❌ Structure analysis error: {e}")
    
    # Try to get PyPDF2 structure info (carefully)
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if page_num < len(reader.pages):
                page = reader.pages[page_num]
                
                # Get rotation safely
                try:
                    result["page_rotation"] = page.rotation
                except:
                    pass
                
                # Count annotations safely
                try:
                    if '/Annots' in page:
                        result["annotations"] = len(page['/Annots'])
                except:
                    pass
                
                # Try to count content streams
                try:
                    if '/Contents' in page:
                        contents = page['/Contents']
                        if isinstance(contents, list):
                            result["content_streams"] = len(contents)
                        else:
                            result["content_streams"] = 1
                except:
                    pass
                    
    except Exception as e:
        print(f"    ⚠️  PyPDF2 structure analysis failed: {e}")
    
    return result

def main():
    if len(sys.argv) != 3:
        print("Usage: python analyze_problematic_page.py <pdf_path> <page_number>")
        print("Page number is 1-based")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    page_number = int(sys.argv[2]) - 1  # Convert to 0-based
    
    if not pdf_path.exists():
        print(f"Error: PDF file {pdf_path} not found")
        sys.exit(1)
    
    print(f"🔍 Analyzing problematic page {page_number + 1} in {pdf_path.name}")
    print("=" * 60)
    
    characteristics = analyze_page_characteristics(pdf_path, page_number)
    
    print("\n📊 Analysis Results:")
    print("=" * 60)
    
    # Print key findings
    if characteristics["pypdf2_hangs"]:
        print("🚨 PROBLEM IDENTIFIED: PyPDF2 hangs on this page!")
    
    if characteristics["pypdf2_timeout"]:
        print("⏰ PyPDF2 times out on this page")
    
    if characteristics["pdfplumber_works"]:
        print("✅ pdfplumber can extract this page successfully")
    
    print(f"\n📋 Page Content Type: {characteristics['page_content_type']}")
    print(f"📊 Has Tables: {characteristics['has_tables']}")
    print(f"🖼️  Has Images: {characteristics['has_images']}")
    print(f"📄 Page Size: {characteristics['page_size']}")
    print(f"🔄 Rotation: {characteristics['page_rotation']}")
    print(f"📝 Annotations: {characteristics['annotations']}")
    print(f"🔢 Content Streams: {characteristics['content_streams']}")
    
    # Save detailed results
    output_file = f"page_analysis_{page_number + 1}.json"
    with open(output_file, 'w') as f:
        json.dump(characteristics, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")
    
    # Generate detection rules
    print("\n🎯 Suggested Detection Rules:")
    if characteristics["pypdf2_hangs"]:
        rules = []
        if characteristics["page_content_type"] == "table_of_contents":
            rules.append("- Detect 'table of contents' pages")
        if characteristics["has_tables"]:
            rules.append("- Detect pages with multiple tables")
        if characteristics["content_streams"] > 1:
            rules.append(f"- Detect pages with {characteristics['content_streams']} content streams")
        if characteristics["annotations"] > 0:
            rules.append(f"- Detect pages with {characteristics['annotations']} annotations")
        
        for rule in rules:
            print(rule)

if __name__ == "__main__":
    main() 