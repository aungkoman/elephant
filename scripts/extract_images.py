"""
extract_images.py
Extracts images from all PDFs in the docs directory and saves them to site/public/images/camps/.
"""
import fitz  # PyMuPDF
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
OUT_DIR = ROOT / "site" / "public" / "images" / "camps"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(name):
    # Keep only alphanumeric characters, spaces, and hyphens
    clean = re.sub(r'[^a-zA-Z0-9\s\-]', '', name)
    # Replace spaces with hyphens and convert to lowercase
    return re.sub(r'\s+', '-', clean.strip()).lower()

pdf_files = list(DOCS_DIR.rglob("*.pdf"))
print(f"Found {len(pdf_files)} PDFs.")

total_extracted = 0

for pdf_path in pdf_files:
    camp_name = pdf_path.stem
    # E.g., "1000Bodhi_ECBT Camp Information" -> "1000bodhi-ecbt-camp-information"
    safe_name = sanitize_filename(camp_name)
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path.name}: {e}")
        continue
        
    img_count = 0
    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Skip very small images (likely icons or logos, unless we want them)
            # Let's say smaller than 10KB is skipped to avoid noise
            if len(image_bytes) < 10240:
                continue
                
            img_count += 1
            total_extracted += 1
            
            out_name = f"{safe_name}-{img_count}.{image_ext}"
            out_path = OUT_DIR / out_name
            
            with open(out_path, "wb") as f:
                f.write(image_bytes)
                
    print(f"Extracted {img_count} images from {pdf_path.name}")

print(f"\nDone. Extracted {total_extracted} total images to {OUT_DIR}")
