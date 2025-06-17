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

# Load environment variables
load_dotenv()

class PDFProcessor:
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=self.api_key)
        self.pdfs_dir = Path('pdfs')
        self.output_dir = Path('output')
        self.summaries_dir = Path('summaries')
        
        # Create directories if they don't exist
        self.output_dir.mkdir(exist_ok=True)
        self.summaries_dir.mkdir(exist_ok=True)
    
    def find_pdf_files(self) -> List[Path]:
        """Find all PDF files in the pdfs directory."""
        if not self.pdfs_dir.exists():
            raise FileNotFoundError(f"Directory {self.pdfs_dir} not found")
        
        pdf_files = list(self.pdfs_dir.glob('*.pdf'))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {self.pdfs_dir}")
        
        # Sort by filename for consistent ordering
        return sorted(pdf_files)
    
    def concatenate_pdfs(self, pdf_files: List[Path]) -> Path:
        """Concatenate multiple PDF files into one."""
        print(f"Concatenating {len(pdf_files)} PDF files...")
        
        merger = PyPDF2.PdfMerger()
        
        for pdf_file in pdf_files:
            print(f"  Adding: {pdf_file.name}")
            with open(pdf_file, 'rb') as file:
                merger.append(file)
        
        output_path = self.output_dir / 'concatenated.pdf'
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()
        print(f"Concatenated PDF saved to: {output_path}")
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
        total_pages = self.count_pages(pdf_path)
        print(f"Total pages: {total_pages}")
        
        if total_pages <= max_pages:
            # Single chunk
            text = self.extract_text_from_pages(pdf_path, 0, total_pages)
            return [(0, total_pages, text)]
        
        chunks = []
        start_page = 0
        
        while start_page < total_pages:
            end_page = min(start_page + max_pages, total_pages)
            text = self.extract_text_from_pages(pdf_path, start_page, end_page)
            chunks.append((start_page, end_page, text))
            
            # Move to next chunk with overlap
            start_page = end_page - overlap
            if start_page >= total_pages:
                break
        
        print(f"Created {len(chunks)} chunks")
        return chunks
    
    def summarize_chunk(self, chunk_text: str, chunk_num: int, total_chunks: int) -> str:
        """Summarize a single chunk using Claude."""
        print(f"Summarizing chunk {chunk_num + 1}/{total_chunks}...")
        
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
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error summarizing chunk {chunk_num + 1}: {e}")
            return f"Error summarizing chunk {chunk_num + 1}: {str(e)}"
    
    def generate_final_summary(self, chunk_summaries: List[str]) -> str:
        """Generate overall summary from chunk summaries."""
        print("Generating final summary...")
        
        combined_summaries = "\n\n".join([f"Chunk {i+1} Summary:\n{summary}" 
                                        for i, summary in enumerate(chunk_summaries)])
        
        prompt = f"""Based on these chunk summaries of a larger document, please provide:

1. **OVERALL SUMMARY**: A comprehensive summary of the entire document set
2. **MAIN THEMES**: The key themes and topics that emerge across all chunks
3. **CRITICAL INSIGHTS**: The most important insights or conclusions

Chunk summaries:
{combined_summaries}"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error generating final summary: {str(e)}"
    
    def extract_timeline(self, chunk_summaries: List[str]) -> str:
        """Extract timeline from chunk summaries."""
        print("Extracting timeline...")
        
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
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error extracting timeline: {str(e)}"
    
    def extract_dramatis_personae(self, chunk_summaries: List[str]) -> str:
        """Extract dramatis personae from chunk summaries."""
        print("Extracting dramatis personae...")
        
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
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error extracting dramatis personae: {str(e)}"
    
    def process_pdfs(self):
        """Main processing function."""
        try:
            # Find PDF files
            pdf_files = self.find_pdf_files()
            print(f"Found {len(pdf_files)} PDF files")
            
            # Concatenate PDFs
            concatenated_pdf = self.concatenate_pdfs(pdf_files)
            
            # Create chunks
            chunks = self.create_chunks(concatenated_pdf)
            
            # Summarize each chunk
            chunk_summaries = []
            for i, (start_page, end_page, text) in enumerate(chunks):
                summary = self.summarize_chunk(text, i, len(chunks))
                chunk_summaries.append(summary)
                
                # Save individual chunk summary
                chunk_file = self.summaries_dir / f'chunk_{i+1}_pages_{start_page+1}-{end_page}.txt'
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    f.write(f"Chunk {i+1} (Pages {start_page+1}-{end_page})\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(summary)
                print(f"Saved: {chunk_file}")
            
            # Generate final summary
            final_summary = self.generate_final_summary(chunk_summaries)
            final_summary_file = self.output_dir / 'final_summary.txt'
            with open(final_summary_file, 'w', encoding='utf-8') as f:
                f.write(final_summary)
            print(f"Saved: {final_summary_file}")
            
            # Extract timeline
            timeline = self.extract_timeline(chunk_summaries)
            timeline_file = self.output_dir / 'timeline.txt'
            with open(timeline_file, 'w', encoding='utf-8') as f:
                f.write(timeline)
            print(f"Saved: {timeline_file}")
            
            # Extract dramatis personae
            dramatis_personae = self.extract_dramatis_personae(chunk_summaries)
            dramatis_file = self.output_dir / 'dramatis_personae.txt'
            with open(dramatis_file, 'w', encoding='utf-8') as f:
                f.write(dramatis_personae)
            print(f"Saved: {dramatis_file}")
            
            print("\nProcessing complete!")
            print(f"Results saved in: {self.output_dir}")
            
        except Exception as e:
            print(f"Error during processing: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    processor = PDFProcessor()
    processor.process_pdfs()

if __name__ == "__main__":
    main() 