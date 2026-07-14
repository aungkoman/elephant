import json
from pathlib import Path

CAMPS_DIR = Path('site/src/content/camps')
for f in CAMPS_DIR.glob('*.json'):
    if f.name == '001.json': continue
    data = json.loads(f.read_text('utf-8'))
    print(f"{data['slug']} -> {data.get('source_dir')}")
