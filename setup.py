#!/usr/bin/env python3
"""
Setup script for PDF Summarization Tool
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def main():
    """Main setup function."""
    print("🚀 Setting up PDF Summarization Tool...")
    
    # Check if virtual environment exists
    venv_path = Path('.venv')
    if not venv_path.exists():
        run_command("python -m venv .venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation command based on OS
    if os.name == 'nt':  # Windows
        activate_cmd = ".venv\\Scripts\\activate"
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source .venv/bin/activate"
        pip_cmd = ".venv/bin/pip"
    
    # Install dependencies
    run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")
    
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        print("🔧 Creating .env file...")
        with open('.env', 'w') as f:
            f.write('# Add your Claude API key here\n')
            f.write('ANTHROPIC_API_KEY=your-api-key-here\n')
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your ANTHROPIC_API_KEY")
    else:
        print("✅ .env file already exists")
    
    # Create pdfs directory
    pdfs_dir = Path('pdfs')
    if not pdfs_dir.exists():
        pdfs_dir.mkdir()
        print("✅ Created pdfs/ directory")
    else:
        print("✅ pdfs/ directory already exists")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your ANTHROPIC_API_KEY")
    print("2. Place PDF files in the pdfs/ directory")
    print("3. Run: python summarize_pdfs.py")
    print(f"\nTo activate virtual environment: {activate_cmd}")

if __name__ == "__main__":
    main() 