import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMPS_DIR = ROOT / 'site' / 'src' / 'content' / 'camps'
IMAGES_DIR = ROOT / 'site' / 'public' / 'images' / 'camps'

def sanitize_filename(name):
    clean = re.sub(r'[^a-zA-Z0-9\s\-]', '', name)
    return re.sub(r'\s+', '-', clean.strip()).lower()

images = list(IMAGES_DIR.glob('*.*'))
print(f"Total images found: {len(images)}")

for f in CAMPS_DIR.glob('*.json'):
    if f.name == '001.json': continue
    data = json.loads(f.read_text('utf-8'))
    
    slug = data['slug']
    source_dir = data.get('source_dir', '')
    
    # E.g., source_dir is "1000Bodhi_ECBT Camp Information" -> "1000bodhi-ecbt" 
    # Let's just use the first word of the source_dir or slug as a prefix to match
    prefix1 = sanitize_filename(source_dir).split('-')[0] if source_dir else slug
    prefix2 = slug.split('-')[0]
    
    # Nay Pyi Taw special case
    if slug == 'nay-pyi-taw':
        prefix1 = 'royalwhiteelephant'
    
    camp_images = []
    for img in images:
        if img.name.startswith(prefix1) or img.name.startswith(prefix2):
            camp_images.append(f"/images/camps/{img.name}")
    
    # Sort them nicely
    camp_images.sort()
    
    data['images'] = camp_images
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Mapped {len(camp_images)} images to {slug}")

