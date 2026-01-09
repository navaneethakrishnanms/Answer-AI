"""
Poppler Setup Script for Windows
Downloads and sets up poppler for PDF processing
"""

import os
import sys
import urllib.request
import zipfile
from pathlib import Path
import shutil

POPPLER_VERSION = "24.08.0-0"
POPPLER_URL = f"https://github.com/oschwartz10612/poppler-windows/releases/download/v{POPPLER_VERSION}/Release-{POPPLER_VERSION}.zip"

def download_poppler():
    """Download poppler for Windows"""
    print("🔽 Downloading poppler for Windows...")
    print(f"   URL: {POPPLER_URL}")
    
    # Create temp directory
    temp_dir = Path("temp_poppler")
    temp_dir.mkdir(exist_ok=True)
    
    zip_path = temp_dir / "poppler.zip"
    
    try:
        # Download with progress
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size))
            sys.stdout.write(f"\r   Progress: {percent}%")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(POPPLER_URL, zip_path, show_progress)
        print("\n✅ Download complete!")
        
        return zip_path, temp_dir
    
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return None, None

def extract_poppler(zip_path, temp_dir):
    """Extract poppler archive"""
    print("\n📦 Extracting poppler...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        print("✅ Extraction complete!")
        return True
    
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def install_poppler(temp_dir):
    """Install poppler to conda environment"""
    print("\n📂 Installing poppler to conda environment...")
    
    # Check if conda environment exists
    conda_prefix = os.environ.get('CONDA_PREFIX')
    
    if not conda_prefix:
        print("⚠️  No conda environment detected!")
        print("   Manual installation required:")
        print(f"   1. Extract poppler to: C:\\poppler")
        print(f"   2. Add to PATH: C:\\poppler\\Library\\bin")
        return False
    
    # Find extracted poppler folder
    extracted_folders = list(temp_dir.glob("poppler-*"))
    if not extracted_folders:
        print("❌ Could not find extracted poppler folder")
        return False
    
    poppler_folder = extracted_folders[0]
    
    # Install to conda environment
    conda_lib_bin = Path(conda_prefix) / "Library" / "bin"
    conda_lib_bin.mkdir(parents=True, exist_ok=True)
    
    # Copy binaries
    source_bin = poppler_folder / "Library" / "bin"
    if source_bin.exists():
        print(f"   Copying files to: {conda_lib_bin}")
        
        for file in source_bin.glob("*"):
            target = conda_lib_bin / file.name
            try:
                if file.is_file():
                    shutil.copy2(file, target)
                    print(f"   ✓ {file.name}")
            except Exception as e:
                print(f"   ⚠️  {file.name}: {e}")
        
        print(f"\n✅ Poppler installed to conda environment!")
        print(f"   Location: {conda_lib_bin}")
        return True
    else:
        print(f"❌ Could not find poppler binaries at: {source_bin}")
        return False

def cleanup(temp_dir):
    """Clean up temporary files"""
    print("\n🧹 Cleaning up...")
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print("✅ Cleanup complete!")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def verify_installation():
    """Verify poppler installation"""
    print("\n🔍 Verifying installation...")
    
    import shutil
    if shutil.which("pdfinfo"):
        print("✅ Poppler is installed and accessible!")
        return True
    else:
        # Check conda environment
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            pdfinfo = Path(conda_prefix) / "Library" / "bin" / "pdfinfo.exe"
            if pdfinfo.exists():
                print("✅ Poppler is installed in conda environment!")
                print(f"   Location: {pdfinfo}")
                return True
        
        print("❌ Poppler not found in PATH")
        print("   You may need to restart your terminal")
        return False

def main():
    print("="*60)
    print("🔧 POPPLER SETUP FOR WINDOWS")
    print("="*60)
    
    # Check if already installed
    if verify_installation():
        print("\n✅ Poppler is already installed!")
        return
    
    # Download
    zip_path, temp_dir = download_poppler()
    if not zip_path:
        return
    
    # Extract
    if not extract_poppler(zip_path, temp_dir):
        cleanup(temp_dir)
        return
    
    # Install
    if not install_poppler(temp_dir):
        cleanup(temp_dir)
        print("\n⚠️  Automatic installation failed")
        print("\n📋 Manual Installation Steps:")
        print("   1. Download poppler from:")
        print(f"      {POPPLER_URL}")
        print("   2. Extract to: C:\\poppler")
        print("   3. Add to PATH: C:\\poppler\\Library\\bin")
        print("   4. Restart terminal")
        return
    
    # Cleanup
    cleanup(temp_dir)
    
    # Verify
    print("\n" + "="*60)
    verify_installation()
    print("="*60)
    print("\n💡 If not detected, restart your terminal and try again")

if __name__ == "__main__":
    main()
