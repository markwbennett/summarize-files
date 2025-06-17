#!/usr/bin/env python3
"""
PDF Summarization Tool
Concatenates PDFs, splits into chunks, and generates summaries using Claude API.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import PyPDF2
from anthropic import Anthropic
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import time

# Load environment variables
load_dotenv()

class PDFProcessor:
    def __init__(self, pdfs_folder: str = None):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Get PDF folder from user input if not provided
        if pdfs_folder is None:
            pdfs_folder = self.get_pdf_folder()
        
        self.pdfs_dir = Path(pdfs_folder)
        # Save outputs in the same folder as the PDFs
        self.output_dir = self.pdfs_dir
        self.summaries_dir = self.pdfs_dir / 'summaries'
        
        # Create summaries subdirectory if it doesn't exist
        self.summaries_dir.mkdir(exist_ok=True)
    
    def get_pdf_folder(self) -> str:
        """Prompt user for PDF folder location."""
        while True:
            folder_path = input("Enter the path to the folder containing PDF files: ").strip()
            
            if not folder_path:
                print("Please enter a valid folder path.")
                continue
            
            # Expand user home directory if needed
            folder_path = os.path.expanduser(folder_path)
            
            if not os.path.exists(folder_path):
                print(f"Folder '{folder_path}' does not exist. Please try again.")
                continue
            
            if not os.path.isdir(folder_path):
                print(f"'{folder_path}' is not a directory. Please try again.")
                continue
            
            # Check if folder contains any PDF files
            pdf_files = list(Path(folder_path).glob('*.pdf'))
            if not pdf_files:
                print(f"No PDF files found in '{folder_path}'. Please try again.")
                continue
            
            print(f"✅ Found {len(pdf_files)} PDF files in '{folder_path}'")
            for pdf in pdf_files[:5]:  # Show first 5 files
                print(f"   📄 {pdf.name}")
            if len(pdf_files) > 5:
                print(f"   ... and {len(pdf_files) - 5} more files")
            return folder_path
    
    def find_pdf_files(self) -> List[Path]:
        """Find all PDF files in the specified directory."""
        pdf_files = list(self.pdfs_dir.glob('*.pdf'))
        # Sort by filename for consistent ordering
        return sorted(pdf_files)
    
    def concatenate_pdfs(self, pdf_files: List[Path]) -> Path:
        """Concatenate multiple PDF files into one."""
        print(f"\n🔗 Concatenating {len(pdf_files)} PDF files...")
        
        merger = PyPDF2.PdfMerger()
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"   📎 Adding ({i}/{len(pdf_files)}): {pdf_file.name}")
            try:
                with open(pdf_file, 'rb') as file:
                    merger.append(file)
            except Exception as e:
                print(f"   ⚠️  Warning: Could not add {pdf_file.name}: {e}")
                continue
        
        output_path = self.output_dir / 'concatenated.pdf'
        print(f"   💾 Saving concatenated PDF...")
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()
        print(f"✅ Concatenated PDF saved to: {output_path.name}")
        return output_path
    
    def count_pages(self, pdf_path: Path) -> int:
        """Count the number of pages in a PDF."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)
    
    def extract_text_from_pages(self, pdf_path: Path, start_page: int, end_page: int) -> str:
        """Extract text from a range of pages."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(start_page, min(end_page, len(reader.pages))):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text
    
    def create_chunks(self, pdf_path: Path, max_pages: int = 100, overlap: int = 10) -> List[Tuple[int, int, str]]:
        """Split PDF into overlapping chunks."""
        print(f"\n📊 Analyzing document structure...")
        total_pages = self.count_pages(pdf_path)
        print(f"   📖 Total pages: {total_pages}")
        
        if total_pages <= max_pages:
            # Single chunk
            print(f"   ✅ Document fits in single chunk (≤{max_pages} pages)")
            print(f"   🔍 Extracting text from all pages...")
            text = self.extract_text_from_pages(pdf_path, 0, total_pages)
            return [(0, total_pages, text)]
        
        print(f"   📚 Document requires chunking (>{max_pages} pages)")
        print(f"   ⚙️  Using {overlap}-page overlap between chunks")
        
        chunks = []
        start_page = 0
        chunk_num = 1
        
        while start_page < total_pages:
            end_page = min(start_page + max_pages, total_pages)
            print(f"   🔍 Extracting chunk {chunk_num} (pages {start_page+1}-{end_page})...")
            text = self.extract_text_from_pages(pdf_path, start_page, end_page)
            chunks.append((start_page, end_page, text))
            
            # Move to next chunk with overlap
            start_page = end_page - overlap
            if start_page >= total_pages:
                break
            chunk_num += 1
        
        print(f"✅ Created {len(chunks)} chunks for processing")
        return chunks
    
    def summarize_chunk(self, chunk_text: str, chunk_num: int, total_chunks: int) -> str:
        """Summarize a single chunk using Claude."""
        print(f"\n🤖 Summarizing chunk {chunk_num + 1}/{total_chunks}...")
        print(f"   📝 Sending to Claude API...")
        
        prompt = f"""Please provide a comprehensive summary of this document chunk ({chunk_num + 1} of {total_chunks}).

Include:
1. Main topics and themes
2. Key events or developments
3. Important people mentioned
4. Significant dates or timeframes
5. Critical decisions or outcomes

Document text:
{chunk_text}"""
        
        try:
            start_time = time.time()
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            elapsed_time = time.time() - start_time
            print(f"   ✅ Summary completed in {elapsed_time:.1f}s")
            return response.content[0].text
        except Exception as e:
            print(f"   ❌ Error summarizing chunk {chunk_num + 1}: {e}")
            return f"Error summarizing chunk {chunk_num + 1}: {str(e)}"
    
    def generate_final_summary(self, chunk_summaries: List[str]) -> str:
        """Generate overall summary from chunk summaries."""
        print(f"\n📋 Generating final comprehensive summary...")
        print(f"   🔄 Combining {len(chunk_summaries)} chunk summaries...")
        
        combined_summaries = "\n\n".join([f"Chunk {i+1} Summary:\n{summary}" 
                                        for i, summary in enumerate(chunk_summaries)])
        
        prompt = f"""Based on these chunk summaries of a larger document, please provide:

1. **OVERALL SUMMARY**: A comprehensive summary of the entire document set
2. **MAIN THEMES**: The key themes and topics that emerge across all chunks
3. **CRITICAL INSIGHTS**: The most important insights or conclusions

Chunk summaries:
{combined_summaries}"""
        
        try:
            print(f"   📝 Sending to Claude API...")
            start_time = time.time()
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            elapsed_time = time.time() - start_time
            print(f"   ✅ Final summary completed in {elapsed_time:.1f}s")
            return response.content[0].text
        except Exception as e:
            print(f"   ❌ Error generating final summary: {e}")
            return f"Error generating final summary: {str(e)}"
    
    def extract_timeline(self, chunk_summaries: List[str]) -> str:
        """Extract timeline from chunk summaries."""
        print(f"\n⏰ Extracting chronological timeline...")
        print(f"   🔍 Analyzing temporal patterns...")
        
        combined_summaries = "\n\n".join([f"Chunk {i+1} Summary:\n{summary}" 
                                        for i, summary in enumerate(chunk_summaries)])
        
        prompt = f"""Based on these document summaries, please extract and create a chronological timeline of events.

Format as:
- Date/Period: Event description
- Date/Period: Event description

Include all significant dates, events, and developments mentioned across all chunks.
If exact dates aren't available, use approximate timeframes or relative chronology.

Chunk summaries:
{combined_summaries}"""
        
        try:
            print(f"   📝 Sending to Claude API...")
            start_time = time.time()
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            elapsed_time = time.time() - start_time
            print(f"   ✅ Timeline extraction completed in {elapsed_time:.1f}s")
            return response.content[0].text
        except Exception as e:
            print(f"   ❌ Error extracting timeline: {e}")
            return f"Error extracting timeline: {str(e)}"
    
    def extract_dramatis_personae(self, chunk_summaries: List[str]) -> str:
        """Extract dramatis personae from chunk summaries."""
        print(f"\n👥 Extracting dramatis personae...")
        print(f"   🔍 Identifying key people and characters...")
        
        combined_summaries = "\n\n".join([f"Chunk {i+1} Summary:\n{summary}" 
                                        for i, summary in enumerate(chunk_summaries)])
        
        prompt = f"""Based on these document summaries, please create a dramatis personae (list of key people/characters).

Format as:
**Name** - Role/Title/Description of their significance and involvement

Include:
- All significant individuals mentioned
- Their roles, titles, or positions
- Brief description of their importance to the events/narrative
- Their relationships to other key figures (if relevant)

Chunk summaries:
{combined_summaries}"""
        
        try:
            print(f"   📝 Sending to Claude API...")
            start_time = time.time()
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            elapsed_time = time.time() - start_time
            print(f"   ✅ Character analysis completed in {elapsed_time:.1f}s")
            return response.content[0].text
        except Exception as e:
            print(f"   ❌ Error extracting dramatis personae: {e}")
            return f"Error extracting dramatis personae: {str(e)}"
    
    def create_pdf_summary(self, title: str, content: str, filename: str) -> Path:
        """Create a PDF file from text content."""
        print(f"   📄 Creating PDF: {filename}")
        
        output_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Build the document
        story = []
        
        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Split content into paragraphs and add to PDF
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Handle bold text formatting
                para = para.replace('**', '<b>').replace('**', '</b>')
                # Create alternating bold tags
                bold_count = para.count('<b>')
                for i in range(0, bold_count, 2):
                    para = para.replace('<b>', '<b>', 1).replace('<b>', '</b>', 1)
                
                story.append(Paragraph(para, styles['Normal']))
                story.append(Spacer(1, 12))
        
        try:
            doc.build(story)
            print(f"   ✅ PDF created: {filename}")
            return output_path
        except Exception as e:
            print(f"   ❌ Error creating PDF {filename}: {e}")
            # Fallback to text file
            text_path = output_path.with_suffix('.txt')
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"{title}\n{'='*len(title)}\n\n{content}")
            print(f"   📝 Saved as text file instead: {text_path.name}")
            return text_path
    
    def process_pdfs(self):
        """Main processing function."""
        try:
            # Find PDF files
            pdf_files = self.find_pdf_files()
            print(f"\n🎯 Processing {len(pdf_files)} PDF files")
            
            # Concatenate PDFs
            concatenated_pdf = self.concatenate_pdfs(pdf_files)
            
            # Create chunks
            chunks = self.create_chunks(concatenated_pdf)
            
            # Summarize each chunk
            print(f"\n🔄 Processing {len(chunks)} chunks...")
            chunk_summaries = []
            for i, (start_page, end_page, text) in enumerate(chunks):
                summary = self.summarize_chunk(text, i, len(chunks))
                chunk_summaries.append(summary)
                
                # Save individual chunk summary as PDF
                chunk_title = f"Chunk {i+1} Summary (Pages {start_page+1}-{end_page})"
                chunk_filename = f'chunk_{i+1}_pages_{start_page+1}-{end_page}_summary.pdf'
                self.create_pdf_summary(chunk_title, summary, chunk_filename)
            
            print(f"\n📊 Generating comprehensive analysis...")
            
            # Generate final summary
            final_summary = self.generate_final_summary(chunk_summaries)
            print(f"   💾 Saving final summary...")
            final_summary_file = self.create_pdf_summary(
                "Comprehensive Document Summary", 
                final_summary, 
                'final_summary.pdf'
            )
            
            # Extract timeline
            timeline = self.extract_timeline(chunk_summaries)
            print(f"   💾 Saving timeline...")
            timeline_file = self.create_pdf_summary(
                "Chronological Timeline", 
                timeline, 
                'timeline.pdf'
            )
            
            # Extract dramatis personae
            dramatis_personae = self.extract_dramatis_personae(chunk_summaries)
            print(f"   💾 Saving dramatis personae...")
            dramatis_file = self.create_pdf_summary(
                "Dramatis Personae", 
                dramatis_personae, 
                'dramatis_personae.pdf'
            )
            
            print(f"\n🎉 Processing complete!")
            print(f"📁 Results saved in: {self.output_dir}")
            print(f"📄 Generated files:")
            print(f"   • Concatenated PDF: concatenated.pdf")
            print(f"   • Final Summary: final_summary.pdf")
            print(f"   • Timeline: timeline.pdf")
            print(f"   • Character List: dramatis_personae.pdf")
            print(f"   • Individual Summaries: {len(chunks)} chunk summary PDFs")
            print(f"   • All files saved to: {self.output_dir.absolute()}")
            
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    print("🚀 PDF Summarization Tool")
    print("=" * 50)
    print("📚 This tool will:")
    print("   • Concatenate your PDF files")
    print("   • Split into chunks if needed (>100 pages)")
    print("   • Generate comprehensive summaries using Claude AI")
    print("   • Create timeline and character analysis")
    print("   • Save all results as PDF files")
    print("=" * 50)
    
    processor = PDFProcessor()
    processor.process_pdfs()

if __name__ == "__main__":
    main() 