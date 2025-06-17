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

1. Run the summarization tool:
   ```bash
   python summarize_pdfs.py
   ```

2. When prompted, enter the path to the folder containing your PDF files
   - Supports paths with spaces: `/Users/username/My Documents/PDFs`
   - Works with or without quotes: `"/path/with spaces"` or `/path/with spaces`
   - Supports relative paths: `./pdfs` or `../documents`
   - Expands home directory: `~/Documents/PDFs`

3. Results will be saved as PDF files in the same folder as your input PDFs

## Output

All output files are saved as PDFs in the same directory as your input files:

- `concatenated.pdf` - Combined PDF file
- `final_summary.pdf` - Comprehensive overall summary
- `timeline.pdf` - Chronological timeline of events
- `dramatis_personae.pdf` - Key people and characters
- `chunk_X_summary.pdf` - Individual chunk summaries (if document was split) 