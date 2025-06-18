#!/usr/bin/env python3
"""
PDF Summarization Tool - Creates PDF chunks for Claude API analysis
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PDFProcessor:
    def __init__(self, pdfs_folder: str = None):
        """Initialize PDF processor with optional folder path."""
        self.pdfs_folder = pdfs_folder
        self.folder_path = None  # Cache the folder path
        self.client = None
        self._setup_anthropic()
        
    def _setup_anthropic(self):
        """Setup Anthropic client."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found in environment variables")
            print("   Please set your API key in a .env file:")
            print("   ANTHROPIC_API_KEY=your_key_here")
            sys.exit(1)
        
        self.client = anthropic.Anthropic(api_key=api_key)
        print("✅ Anthropic client initialized")
    
    def get_pdf_folder(self) -> str:
        """Get PDF folder path from user or use provided one."""
        if self.folder_path:
            return self.folder_path
            
        if self.pdfs_folder:
            folder_path = Path(self.pdfs_folder)
            if folder_path.exists():
                self.folder_path = str(folder_path)
                return self.folder_path
            else:
                print(f"❌ Provided folder does not exist: {self.pdfs_folder}")
        
        # Ask user for folder
        while True:
            folder_input = input("\n📁 Enter the path to your PDFs folder: ").strip()
            
            # Remove quotes if present
            folder_input = folder_input.strip('"\'')
            
            folder_path = Path(folder_input).expanduser().resolve()
            
            if folder_path.exists() and folder_path.is_dir():
                print(f"✅ Using folder: {folder_path}")
                self.folder_path = str(folder_path)
                return self.folder_path
            else:
                print(f"❌ Folder not found: {folder_path}")
                print("   Please check the path and try again.")

    def find_pdf_files(self) -> List[Path]:
        """Find all PDF files in the specified folder."""
        folder = Path(self.get_pdf_folder())
        pdf_files = list(folder.glob("*.pdf"))
        
        # Filter out our own generated files
        excluded_patterns = ['chunk_', 'concatenated', '_summary.pdf', '_timeline.pdf', '_dramatis_personae.pdf']
        original_pdfs = []
        for pdf in pdf_files:
            if not any(pattern in pdf.name for pattern in excluded_patterns):
                original_pdfs.append(pdf)
        
        if not original_pdfs:
            print(f"❌ No original PDF files found in {folder}")
            # Check if there's a PDFs subdirectory
            pdfs_subdir = folder / "PDFs"
            if pdfs_subdir.exists():
                print(f"💡 Found a 'PDFs' subdirectory. Try using: {pdfs_subdir}")
            sys.exit(1)
        
        print(f"📚 Found {len(original_pdfs)} original PDF file(s):")
        for pdf in original_pdfs:
            print(f"   📄 {pdf.name}")
        
        return original_pdfs

    def concatenate_pdfs(self, pdf_files: List[Path]) -> Path:
        """Concatenate multiple PDFs into one."""
        if len(pdf_files) == 1:
            print(f"📄 Using single PDF: {pdf_files[0].name}")
            return pdf_files[0]
        
        print(f"🔗 Concatenating {len(pdf_files)} PDFs...")
        
        output_path = pdf_files[0].parent / "concatenated_document.pdf"
        
        merger = PyPDF2.PdfMerger()
        
        for pdf_file in pdf_files:
            print(f"   ➕ Adding {pdf_file.name}")
            try:
                merger.append(pdf_file)
            except Exception as e:
                print(f"   ⚠️  Error adding {pdf_file.name}: {e}")
                print(f"   🔄 Trying to add pages individually...")
                try:
                    # Try to add pages one by one
                    with open(pdf_file, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page_num in range(len(reader.pages)):
                            try:
                                merger.append(pdf_file, pages=(page_num, page_num + 1))
                            except Exception as page_error:
                                print(f"   ⚠️  Skipping page {page_num + 1} of {pdf_file.name}: {page_error}")
                                continue
                    print(f"   ✅ Added {pdf_file.name} page by page")
                except Exception as fallback_error:
                    print(f"   ❌ Could not add {pdf_file.name} at all: {fallback_error}")
                    continue
        
        try:
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
            
            merger.close()
            print(f"✅ Concatenated PDF created: {output_path.name}")
            return output_path
        except Exception as e:
            print(f"❌ Error writing concatenated PDF: {e}")
            merger.close()
            # If concatenation fails completely, just use the first PDF
            print(f"🔄 Falling back to using first PDF: {pdf_files[0].name}")
            return pdf_files[0]

    def count_pages(self, pdf_path: Path) -> int:
        """Count total pages in PDF."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)

    def create_pdf_chunks(self, pdf_path: Path, max_pages: int = 30, overlap: int = 5) -> List[Path]:
        """Create PDF chunks by copying pages."""
        print(f"\n📊 Creating PDF chunks...")
        total_pages = self.count_pages(pdf_path)
        print(f"   📖 Total pages: {total_pages}")
        
        if total_pages <= max_pages:
            print(f"   ✅ Document fits in single chunk ({total_pages} pages)")
            return [pdf_path]
        
        chunks = []
        chunk_num = 1
        start_page = 0
        
        while start_page < total_pages:
            end_page = min(start_page + max_pages, total_pages)
            
            print(f"   📄 Creating chunk {chunk_num}: pages {start_page + 1}-{end_page}")
            
            # Create chunk filename
            chunk_filename = f"chunk_{chunk_num:02d}_pages_{start_page + 1:03d}-{end_page:03d}.pdf"
            chunk_path = pdf_path.parent / chunk_filename
            
            # Copy pages to chunk
            self._create_pdf_chunk(pdf_path, chunk_path, start_page, end_page)
            chunks.append(chunk_path)
            
            # Move to next chunk with overlap
            start_page += max_pages - overlap
            chunk_num += 1
        
        print(f"✅ Created {len(chunks)} PDF chunks")
        return chunks

    def _create_pdf_chunk(self, source_pdf: Path, output_pdf: Path, start_page: int, end_page: int):
        """Create a PDF chunk by copying specific pages."""
        with open(source_pdf, 'rb') as source_file:
            reader = PyPDF2.PdfReader(source_file)
            writer = PyPDF2.PdfWriter()
            
            # Copy pages
            for page_num in range(start_page, min(end_page, len(reader.pages))):
                page = reader.pages[page_num]
                writer.add_page(page)
            
            # Write chunk
            with open(output_pdf, 'wb') as output_file:
                writer.write(output_file)
            
            # Check file size and warn if over Claude's limit (accounting for base64 encoding +33%)
            file_size_mb = output_pdf.stat().st_size / (1024 * 1024)
            encoded_size_mb = file_size_mb * 1.33  # Base64 encoding overhead
            if encoded_size_mb > 32:
                print(f"   ⚠️  Warning: {output_pdf.name} is {file_size_mb:.1f}MB ({encoded_size_mb:.1f}MB encoded - over Claude's 32MB limit)")
            elif encoded_size_mb > 28:
                print(f"   ⚠️  {output_pdf.name} is {file_size_mb:.1f}MB ({encoded_size_mb:.1f}MB encoded - approaching limit)")
            else:
                print(f"   ✅ {output_pdf.name} is {file_size_mb:.1f}MB ({encoded_size_mb:.1f}MB encoded)")

    def _cleanup_previous_outputs(self):
        """Remove previous output files."""
        folder = Path(self.get_pdf_folder())
        
        patterns = [
            "chunk_*.pdf",
            "concatenated_document.pdf",
            "*_summary.pdf",
            "*_timeline.pdf", 
            "*_dramatis_personae.pdf"
        ]
        
        removed_count = 0
        for pattern in patterns:
            for file in folder.glob(pattern):
                try:
                    file.unlink()
                    removed_count += 1
                except Exception as e:
                    print(f"⚠️  Could not remove {file.name}: {e}")
        
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} previous output files")

    def analyze_pdf_chunk(self, chunk_path: Path, chunk_num: int, total_chunks: int, previous_summary: str = "") -> str:
        """Send PDF chunk to Claude for analysis with previous context."""
        print(f"🤖 Analyzing chunk {chunk_num}/{total_chunks} with Claude...")
        
        # Read PDF as bytes and encode to base64
        import base64
        with open(chunk_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Build context-aware prompt
        if previous_summary and chunk_num > 1:
            context_text = f"""Please analyze this PDF document (chunk {chunk_num} of {total_chunks}) and provide a comprehensive summary that builds upon the previous analysis.

PREVIOUS SUMMARY FROM EARLIER CHUNKS:
{previous_summary}

For this new chunk, please:
1. Summarize the key points, important details, dates, names, and significant information
2. Note any connections or continuations from the previous chunks
3. Identify any new developments or information not covered in previous summaries
4. Be thorough and detailed while building a coherent narrative

Focus on this chunk's content while maintaining awareness of the overall document context."""
        else:
            context_text = f"Please provide a comprehensive summary of this PDF document (chunk {chunk_num} of {total_chunks}). Include key points, important details, dates, names, and any significant information. Be thorough and detailed."
        
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text",
                                "text": context_text
                            }
                        ]
                    }
                ]
            )
            
            end_time = time.time()
            print(f"   ✅ Claude analysis completed in {end_time - start_time:.1f}s")
            
            return response.content[0].text
            
        except Exception as e:
            print(f"   ❌ Claude API error: {e}")
            return f"Error analyzing chunk {chunk_num}: {str(e)}"

    def generate_final_summary(self, chunk_summaries: List[str]) -> str:
        """Generate final summary from all chunks."""
        print(f"📝 Generating final summary from {len(chunk_summaries)} chunks...")
        
        combined_summaries = "\n\n".join([
            f"CHUNK {i+1} SUMMARY:\n{summary}" 
            for i, summary in enumerate(chunk_summaries)
        ])
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Based on these chunk summaries from a document, please create a comprehensive final summary that synthesizes all the information:

{combined_summaries}

Please provide:
1. An executive summary
2. Key findings and main points
3. Important details and context
4. Any conclusions or recommendations

Make this a cohesive, well-structured summary that captures the essence of the entire document."""
                    }
                ]
            )
            
            print("   ✅ Final summary generated")
            return response.content[0].text
            
        except Exception as e:
            print(f"   ❌ Error generating final summary: {e}")
            return f"Error generating final summary: {str(e)}"

    def extract_timeline(self, chunk_summaries: List[str]) -> str:
        """Extract timeline from summaries."""
        print("📅 Extracting timeline...")
        
        combined_summaries = "\n\n".join(chunk_summaries)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""From the following document summaries, please extract and create a chronological timeline of all events, dates, and time-based information mentioned:

{combined_summaries}

Format the timeline as:
- Date/Time: Event description
- Date/Time: Event description

Include all dates, deadlines, meetings, events, and temporal references. If exact dates aren't available, use approximate timeframes mentioned."""
                    }
                ]
            )
            
            print("   ✅ Timeline extracted")
            return response.content[0].text
            
        except Exception as e:
            print(f"   ❌ Error extracting timeline: {e}")
            return f"Error extracting timeline: {str(e)}"

    def extract_dramatis_personae(self, chunk_summaries: List[str]) -> str:
        """Extract list of people/entities."""
        print("👥 Extracting dramatis personae...")
        
        combined_summaries = "\n\n".join(chunk_summaries)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""From the following document summaries, please create a dramatis personae - a comprehensive list of all people, organizations, companies, and entities mentioned:

{combined_summaries}

Format as:
**PEOPLE:**
- Name: Role/Description/Relevance

**ORGANIZATIONS/COMPANIES:**
- Name: Description/Role

**OTHER ENTITIES:**
- Name: Description

Include everyone and everything mentioned, with their roles and relevance to the document."""
                    }
                ]
            )
            
            print("   ✅ Dramatis personae extracted")
            return response.content[0].text
            
        except Exception as e:
            print(f"   ❌ Error extracting dramatis personae: {e}")
            return f"Error extracting dramatis personae: {str(e)}"

    def create_pdf_summary(self, title: str, content: str, filename: str) -> Path:
        """Create a formatted PDF from text content."""
        folder = Path(self.get_pdf_folder())
        output_path = folder / filename
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = styles['Title']
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Content
        content_style = styles['Normal']
        
        # Split content into paragraphs and format
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Handle bullet points and formatting
                if para.strip().startswith('- ') or para.strip().startswith('* '):
                    para = para.replace('- ', '• ').replace('* ', '• ')
                
                story.append(Paragraph(para.strip(), content_style))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        return output_path

    def process_pdfs(self):
        """Main processing function."""
        print("🚀 Starting PDF summarization process...")
        
        # Cleanup previous outputs
        self._cleanup_previous_outputs()
        
        # Find and concatenate PDFs
        pdf_files = self.find_pdf_files()
        concatenated_pdf = self.concatenate_pdfs(pdf_files)
        
        # Create PDF chunks (30 pages with 5-page overlap for coherent summaries)
        chunk_paths = self.create_pdf_chunks(concatenated_pdf, max_pages=30, overlap=5)
        
        # Analyze each chunk with cumulative context
        chunk_summaries = []
        cumulative_summary = ""
        
        for i, chunk_path in enumerate(chunk_paths, 1):
            summary = self.analyze_pdf_chunk(chunk_path, i, len(chunk_paths), cumulative_summary)
            chunk_summaries.append(summary)
            
            # Update cumulative summary for next chunk
            if cumulative_summary:
                cumulative_summary += f"\n\nCHUNK {i} SUMMARY:\n{summary}"
            else:
                cumulative_summary = f"CHUNK {i} SUMMARY:\n{summary}"
        
        # Generate outputs
        print(f"\n📋 Generating final outputs...")
        
        final_summary = self.generate_final_summary(chunk_summaries)
        timeline = self.extract_timeline(chunk_summaries)
        dramatis_personae = self.extract_dramatis_personae(chunk_summaries)
        
        # Create PDF outputs
        folder = Path(self.get_pdf_folder())
        base_name = concatenated_pdf.stem
        
        summary_pdf = self.create_pdf_summary(
            f"Summary: {base_name}", 
            final_summary, 
            f"{base_name}_summary.pdf"
        )
        
        timeline_pdf = self.create_pdf_summary(
            f"Timeline: {base_name}", 
            timeline, 
            f"{base_name}_timeline.pdf"
        )
        
        dramatis_pdf = self.create_pdf_summary(
            f"Dramatis Personae: {base_name}", 
            dramatis_personae, 
            f"{base_name}_dramatis_personae.pdf"
        )
        
        print(f"\n🎉 Processing complete! Generated files:")
        print(f"   📄 Summary: {summary_pdf.name}")
        print(f"   📅 Timeline: {timeline_pdf.name}")
        print(f"   👥 Dramatis Personae: {dramatis_pdf.name}")
        print(f"   🗂️  PDF Chunks: {len(chunk_paths)} files")

def main():
    """Main entry point."""
    processor = PDFProcessor()
    processor.process_pdfs()

if __name__ == "__main__":
    main() 