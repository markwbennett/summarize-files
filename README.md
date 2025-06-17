# PDF Summarization Tool

A tool to concatenate multiple PDFs, split them into manageable chunks, and generate summaries using Claude API.

## Features

- Concatenate multiple PDF files
- Split large documents into overlapping chunks (max 100 pages per chunk)
- Generate individual document summaries
- Create overall summary of entire document set
- Extract timeline and dramatis personae

## Setup

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Claude API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

## Usage

1. Place PDF files in the `pdfs/` directory
2. Run the summarization tool:
   ```bash
   python summarize_pdfs.py
   ```

3. Results will be saved in the `output/` directory

## Output

- `concatenated.pdf` - Combined PDF file
- `summaries/` - Individual chunk summaries
- `final_summary.txt` - Overall summary
- `timeline.txt` - Extracted timeline
- `dramatis_personae.txt` - Character/person list 