"""Parse all ECBT camp PDFs into structured JSON."""
import os, json, re, glob

def read(path):
    with open(path, 'r', encoding='latin-1') as f:
        return f.read()

def between(text, start, end=None):
    """Return text between start and end markers (case-insensitive)."""
    si = text.lower().find(start.lower())
    if si < 0:
        return None
    chunk = text[si + len(start):]
    if end:
        ei = chunk.lower().find(end.lower())
        if ei >= 0:
            chunk = chunk[:ei]
    return chunk.strip()

def dms_to_decimal(dms):
    """Convert DMS like '18°24\\'44.44\"N' to decimal."""
    m = re.search(r"([\d.]+)\s*°\s*([\d.]+)\s*'\s*([\d.]+)\s*\"", dms)
    if m:
        return float(m.group(1)) + float(m.group(2))/60 + float(m.group(3))/3600
    return None

def coord(text):
    # Try DMS format first
    lat_dms = re.search(r'Latitude\s*([\d.]+\s*°\s*[\d.]+\s*\'?\s*[\d.]+\s*\"?\s*N)', text, re.I)
    lon_dms = re.search(r'Longitude\s*([\d.]+\s*°\s*[\d.]+\s*\'?\s*[\d.]+\s*\"?\s*E)', text, re.I)
    lat = dms_to_decimal(lat_dms.group(1)) if lat_dms else None
    lon = dms_to_decimal(lon_dms.group(1)) if lon_dms else None
    if lat and lon:
        return (str(lat), str(lon))
    # Fallback: decimal format
    lat = re.search(r'Latitude.*?([\d.]+)', text, re.I)
    lon = re.search(r'Longitude.*?([\d.]+)', text, re.I)
    return (lat.group(1) if lat else None, lon.group(1) if lon else None)

def elephants(text):
    """Parse compound area and elephant numbers."""
    section = between(text, 'Compound Area', 'Location map') or between(text, 'Compound Area&', 'Location map') or between(text, 'Compound Area', 'Fees') or between(text, 'Compound Area&', 'Fees') or between(text, 'Compound Area', 'Map') or ''
    area = re.search(r'(?:Camp )?Area\s*[-:]\s*(.+?)(?:\n|$)', section, re.I)
    total = re.search(r'(?:Total|Camp [Ee]lephants?)\s*[-:].*?(\d+)', section)
    if not total:
        total = re.search(r'(\d+)\s*(?:\(?male\)?\s*elephants?|[Ee]lephant)', section)
    male = re.search(r'(\d+)\s*\(?\s*male', section, re.I)
    female = re.search(r'(\d+)\s*\(?\s*female', section, re.I)
    # Also try "X male and Y female"
    both = re.search(r'(\d+)\s*male\s*(?:and|&)\s*(\d+)\s*female', section, re.I)
    return {
        'area': area.group(1).strip().rstrip('.-') if area else None,
        'total_elephants': int(total.group(1)) if total else (int(both.group(1)) + int(both.group(2)) if both else None),
        'male_elephants': int(male.group(1)) if male else (int(both.group(1)) if both else None),
        'female_elephants': int(female.group(1)) if female else (int(both.group(2)) if both else None),
    }

def fees(text):
    section = between(text, 'Fees for', 'Monks') or between(text, 'Fees for', 'Opening hours') or ''
    if not section:
        return None
    entry_local = re.search(r'Entrance\s*fee.*?(?:Local|[-–])\s*(\d+)\s*MMK', section, re.I)
    entry_foreign = re.search(r'Entrance\s*fee.*?(?:Foreigner|Foreign).*?(\d+)\s*MMK', section, re.I)
    ride_local = re.search(r'(?:Elephant\s*)?Riding\s*fee.*?(?:Local|[-–])\s*(\d+)\s*MMK', section, re.I)
    ride_foreign = re.search(r'(?:Elephant\s*)?Riding\s*fee.*?(?:Foreigner|Foreign).*?(\d+)\s*MMK', section, re.I)
    return {
        'entrance_fee_local_mmk': int(entry_local.group(1)) if entry_local else None,
        'entrance_fee_foreigner_mmk': int(entry_foreign.group(1)) if entry_foreign else None,
        'elephant_riding_fee_local_mmk': int(ride_local.group(1)) if ride_local else None,
        'elephant_riding_fee_foreigner_mmk': int(ride_foreign.group(1)) if ride_foreign else None,
    }

def activities(text):
    section = between(text, 'Fees for', None) or text
    acts = []
    keywords = ['Elephant Riding', 'Elephant Feeding', 'Elephant Buffet', 'Elephant Bathing',
                'Elephant Show', 'Photography', 'Trekking', 'Bird Watching', 'Camping',
                'Rafting', 'Canoeing', 'Fishing', 'Sightseeing', 'Jungle Walk', 'Nature Walk',
                'Boat', 'Swimming', 'Shopping', 'Souvenir', 'Restaurant', 'Pre Wedding',
                'Wedding', 'Hiking', 'Relax', 'Shelter', 'Conservation', 'Education',
                'Elephant Training', 'Video Recording', 'Buffet Feeding', 'Donate']
    for line in section.split('\n'):
        for kw in keywords:
            if kw.lower() in line.lower() and kw not in acts:
                acts.append(kw)
    return acts[:20] if acts else None

def contacts(text):
    phones = re.findall(r'Ph[:\s]*([\d\-\s/]+)', text)
    # Also match 09-XXXXXXXX patterns
    more = re.findall(r'09[\-\s]?\d{5,8}', text)
    return list(set(phones + more)) if (phones or more) else None

def camp_name(text, filename):
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
    # Prefer lines with "Elephant Camp" or "Elephant Conservation Camp"
    for l in lines[:30]:
        if re.search(r'(Elephant (Conservation )?Camp|Elephants? Conservation Garden)', l, re.I) and 'Ministry' not in l and 'Timber' not in l and 'Tourism' not in l:
            return ' '.join(l.split())
    # Fallback
    return filename.split('__')[0].replace('_ECBT Camp Information', '').replace('_', ' ')

def parse_one(filepath):
    text = read(filepath)
    filename = os.path.basename(filepath)
    lat, lon = coord(text)
    ele = elephants(text)
    fee = fees(text)
    act = activities(text)
    ph = contacts(text)
    name = camp_name(text, filename)

    # Ministry / Agency from header
    header = text[:600]
    ministry_line = None
    for line in text.split('\n')[:10]:
        if 'Ministry' in line:
            ministry_line = line.strip()
            break
    agency = None
    for line in text.split('\n')[:15]:
        stripped = line.strip()
        if 'Extraction Agency' in stripped or 'Region' in stripped:
            agency = stripped
            break
    mte = 'Myanma Timber Enterprise' if 'Myanma Timber Enterprise' in header else None

    # Location
    loc = between(text, 'Camp Location', 'Way & Duration') or \
          between(text, 'Location', 'Way & Duration') or \
          between(text, '(A)Camp Location', '(B)')

    # Access
    acc = between(text, 'Way & Duration', 'Compound Area') or \
          between(text, '(B)Way', '(C)')

    # Opening hours
    hours = re.search(r'Opening hours\s*[:\-]\s*(.+?)(?:\n|$)', text, re.I)

    return {
        'camp_name': name.strip(),
        'source_file': filename,
        'ministry': ministry_line,
        'extraction_agency': agency or mte,
        'location_description': loc.strip() if loc else None,
        'latitude': lat,
        'longitude': lon,
        'access': acc.strip() if acc else None,
        'compound_area': ele['area'],
        'total_elephants': ele['total_elephants'],
        'male_elephants': ele['male_elephants'],
        'female_elephants': ele['female_elephants'],
        'opening_hours': hours.group(1).strip() if hours else None,
        'fees': fee,
        'activities': act,
        'contact_phones': ph,
    }

def main():
    all_entries = []
    for f in sorted(glob.glob('extracted_texts/*.txt')):
        try:
            entry = parse_one(f)
            # Determine language
            fname = os.path.basename(f)
            if 'English' in fname:
                entry['language'] = 'English'
            elif 'Myanmar' in fname:
                entry['language'] = 'Myanmar'
            else:
                entry['language'] = 'Bilingual'
            all_entries.append(entry)
        except Exception as e:
            all_entries.append({'source_file': os.path.basename(f), 'error': str(e)})

    # Merge by camp directory: prefer English, fallback Myanmar
    groups = {}
    for e in all_entries:
        key = e.get('source_file','').split('__')[0]
        groups.setdefault(key, []).append(e)

    camps = []
    for key, entries in groups.items():
        eng = next((e for e in entries if e.get('language')=='English'), None)
        mya = next((e for e in entries if e.get('language')=='Myanmar'), None)
        bi  = next((e for e in entries if e.get('language')=='Bilingual'), None)
        best = eng or bi or mya or entries[0]

        camps.append({
            'camp_directory': key,
            'camp_name': best.get('camp_name'),
            'ministry': best.get('ministry'),
            'extraction_agency': best.get('extraction_agency'),
            'location_description': best.get('location_description'),
            'latitude': best.get('latitude'),
            'longitude': best.get('longitude'),
            'access': best.get('access'),
            'compound_area': best.get('compound_area'),
            'total_elephants': best.get('total_elephants'),
            'male_elephants': best.get('male_elephants'),
            'female_elephants': best.get('female_elephants'),
            'opening_hours': best.get('opening_hours'),
            'fees': best.get('fees'),
            'activities': best.get('activities'),
            'contact_phones': best.get('contact_phones'),
            'languages_available': [e.get('language') for e in entries],
        })

    output = {'total_camps': len(camps), 'total_pdfs': len(all_entries), 'camps': camps}
    with open('ecbt_camps.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f'Done: {len(camps)} camps from {len(all_entries)} PDFs -> ecbt_camps.json')

if __name__ == '__main__':
    main()
