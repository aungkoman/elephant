"""Parse extracted PDF texts into a structured JSON of ECBT camp information."""
import os, json, re, glob

def read_text(path):
    with open(path, 'r', encoding='latin-1') as f:
        return f.read()

def clean_line(s):
    return s.strip().replace('\f', '')

def extract_camp_name(text):
    """Heuristic: find the camp name line before 'Camp Location' or near top."""
    lines = [clean_line(l) for l in text.split('\n') if clean_line(l)]
    # Look for pattern: "<Name> Elephant Conservation Camp" or similar
    for i, line in enumerate(lines):
        if 'Elephant Conservation Camp' in line or 'Elephant Camp' in line:
            return line.strip()
        if 'Royal White Elephants Conservation Garden' in line:
            return line.strip()
    return None

def extract_section(text, start_pattern, end_pattern=None):
    """Extract lines between start_pattern and end_pattern."""
    lines = text.split('\n')
    start_idx = None
    for i, line in enumerate(lines):
        if start_pattern.lower() in clean_line(line).lower():
            start_idx = i + 1
            break
    if start_idx is None:
        return []
    result = []
    for j in range(start_idx, len(lines)):
        if end_pattern and end_pattern.lower() in clean_line(lines[j]).lower():
            break
        result.append(clean_line(lines[j]))
    return [r for r in result if r]

def extract_location(text):
    """Extract location section."""
    section = extract_section(text, 'Location', 'Way & Duration')
    if not section:
        section = extract_section(text, 'Location', 'Compound Area')
    if not section:
        section = extract_section(text, 'Camp Location', 'Way')
    if not section:
        section = extract_section(text, '(A)Camp Location', '(B)')
    return '\n'.join(section) if section else None

def extract_coordinates(text):
    """Extract lat/long from text."""
    lat = None
    lon = None
    for line in text.split('\n'):
        line = clean_line(line)
        lat_m = re.search(r'Latitude.*?(\d+[\.\d]*°?\s*\d*[\.\']*\d*[\.\"]*\s*[N]?)', line, re.IGNORECASE)
        lon_m = re.search(r'Longitude.*?(\d+[\.\d]*°?\s*\d*[\.\']*\d*[\.\"]*\s*[E]?)', line, re.IGNORECASE)
        if lat_m:
            lat = lat_m.group(1).strip()
        if lon_m:
            lon = lon_m.group(1).strip()
    return lat, lon

def extract_access(text):
    """Extract way/duration for visitation."""
    section = extract_section(text, 'Way & Duration', 'Compound Area')
    if not section:
        section = extract_section(text, 'Way & Duration for visitation', 'Compound')
    if not section:
        section = extract_section(text, '(B)Way', '(C)')
    return '\n'.join(section) if section else None

def extract_compound(text):
    """Extract compound area and elephant numbers."""
    section = extract_section(text, 'Compound Area', 'Location map')
    if not section:
        section = extract_section(text, 'Compound Area&', 'Location map')
    if not section:
        section = extract_section(text, '(C)Compound', '(D)')
    if not section:
        section = extract_section(text, '(C)Compound Area', 'Location map')

    area = None
    total_elephants = None
    male = None
    female = None
    for line in (section or []):
        area_m = re.search(r'Area\s*[-:]\s*(.+?)(?:$|\.)', line, re.IGNORECASE)
        if area_m:
            area = area_m.group(1).strip()
        ele_m = re.search(r'(?:Total|Camp elephants)\s*[-:].*?(\d+)\s*(?:elephants|head)', line, re.IGNORECASE)
        if ele_m:
            total_elephants = int(ele_m.group(1))
        male_m = re.search(r'(\d+)\s*\(?\s*male', line, re.IGNORECASE)
        if male_m:
            male = int(male_m.group(1))
        female_m = re.search(r'(\d+)\s*\(?\s*female', line, re.IGNORECASE)
        if female_m:
            female = int(female_m.group(1))
    return {
        'area': area,
        'total_elephants': total_elephants,
        'male_elephants': male,
        'female_elephants': female
    }

def extract_activities(text):
    """Extract activities/services offered."""
    activities = []
    # Look for patterns like "Elephant Riding", "Feeding", etc.
    keywords = [
        'Elephant Riding', 'Feeding Elephants', 'Elephant Feeding',
        'Bathing', 'Elephant Bathing', 'Photo', 'Photography',
        'Trekking', 'Bird Watching', 'Camping', 'Rafting',
        'Pre Wedding', 'Wedding', 'Relax', 'Shelter',
        'Elephant Show', 'Canoeing', 'Fishing', 'Sightseeing',
        'Walking', 'Jungle Walk', 'Nature Walk', 'Boat',
        'Swimming', 'Shopping', 'Souvenir', 'Restaurant',
        'Education', 'Conservation', 'Hiking'
    ]
    for line in text.split('\n'):
        line = clean_line(line)
        for kw in keywords:
            if kw.lower() in line.lower() and kw not in activities:
                activities.append(kw)
    return activities[:15]  # cap

def extract_management(text):
    """Extract management/ministry info."""
    lines = [clean_line(l) for l in text.split('\n')[:15]]
    ministry = None
    agency = None
    for line in lines:
        if 'Ministry' in line:
            ministry = line.strip()
        if 'Extraction Agency' in line or 'Extraction' in line:
            agency = line.strip()
        if 'Myanmar Timber Enterprise' in line:
            agency = line.strip()
    return {'ministry': ministry, 'agency': agency}

def extract_contact(text):
    """Extract phone numbers."""
    phones = re.findall(r'(?:Ph|Phone)[:\s]*([\d\-\s/]+(?:\))?)', text)
    return [p.strip() for p in phones] if phones else []

def extract_elephant_details(text):
    """For Royal White Elephant and similar detail-heavy files."""
    elephants = []
    # Look for numbered detail blocks
    current = {}
    lines = text.split('\n')
    for line in lines:
        line = clean_line(line)
        name_match = re.match(r'\(\d+\)\s*Sex\s+(.+)', line)
        if name_match:
            if current:
                elephants.append(current)
            current = {'name': name_match.group(1).strip()}
            continue
        if not current:
            continue
        # Match detail fields
        field_match = re.match(r'\(\d+\)\s*(\w[\w\s]+?)\s{2,}(.+)', line)
        if field_match:
            key = field_match.group(1).strip().lower().replace(' ', '_')
            val = field_match.group(2).strip()
            current[key] = val
        # Handle continuation lines
        elif current and line and not line.startswith('('):
            keys = list(current.keys())
            if keys:
                last_key = keys[-1]
                current[last_key] += ' ' + line
    if current:
        elephants.append(current)
    return elephants if elephants else None

def parse_pdf_file(filepath):
    """Parse a single extracted text file."""
    text = read_text(filepath)
    filename = os.path.basename(filepath)

    camp_name = extract_camp_name(text) or filename.replace('.txt', '').replace('__', ' - ')
    lat, lon = extract_coordinates(text)
    location = extract_location(text)
    access = extract_access(text)
    compound = extract_compound(text)
    activities = extract_activities(text)
    management = extract_management(text)
    contact = extract_contact(text)
    elephant_details = extract_elephant_details(text)

    # clean up camp name
    camp_name = camp_name.replace('\\t', '').strip()

    return {
        'camp_name': camp_name,
        'source_file': filename,
        'ministry': management.get('ministry'),
        'extraction_agency': management.get('agency'),
        'location_description': location,
        'latitude': lat,
        'longitude': lon,
        'access': access,
        'compound_area': compound['area'],
        'total_elephants': compound['total_elephants'],
        'male_elephants': compound['male_elephants'],
        'female_elephants': compound['female_elephants'],
        'activities': activities if activities else None,
        'contact_phones': contact if contact else None,
        'elephant_details': elephant_details,
        'raw_text_preview': text[:500].strip() if not management.get('ministry') else None
    }

def main():
    base_dir = 'extracted_texts'
    all_camps = []

    for txt_file in sorted(glob.glob(f'{base_dir}/*.txt')):
        try:
            data = parse_pdf_file(txt_file)
            all_camps.append(data)
        except Exception as e:
            all_camps.append({
                'camp_name': txt_file,
                'error': str(e)
            })

    # Group by camp directory (pairs of English/Myanmar)
    # Build a summary by camp
    camps_by_name = {}
    for entry in all_camps:
        # Derive camp key from filename
        fname = entry.get('source_file', '')
        parts = fname.split('__')
        if len(parts) >= 1:
            camp_key = parts[0]  # e.g., "Mokka_ECBT Camp Information"
        else:
            camp_key = fname

        if camp_key not in camps_by_name:
            camps_by_name[camp_key] = {
                'camp_directory': camp_key,
                'versions': []
            }
        camps_by_name[camp_key]['versions'].append(entry)

    # Determine language for each version
    for camp in camps_by_name.values():
        for v in camp['versions']:
            fname = v.get('source_file', '')
            if 'English' in fname:
                v['language'] = 'English'
            elif 'Myanmar' in fname:
                v['language'] = 'Myanmar'
            else:
                v['language'] = 'Bilingual'

    # Merge: prefer English version data, fall back to Myanmar
    final_camps = []
    for camp_key, camp_data in camps_by_name.items():
        eng = None
        mya = None
        bi = None
        for v in camp_data['versions']:
            if v.get('language') == 'English':
                eng = v
            elif v.get('language') == 'Myanmar':
                mya = v
            elif v.get('language') == 'Bilingual':
                bi = v

        best = eng or bi or mya or camp_data['versions'][0]
        merged = {
            'camp_directory': camp_key,
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
            'activities': best.get('activities'),
            'contact_phones': best.get('contact_phones'),
            'elephant_details': best.get('elephant_details'),
            'versions_available': [v.get('language') for v in camp_data['versions']],
            'raw_english_entries': [v for v in camp_data['versions'] if v.get('language') == 'English'],
            'raw_myanmar_entries': [v for v in camp_data['versions'] if v.get('language') == 'Myanmar'],
        }
        final_camps.append(merged)

    output = {
        'total_camps': len(final_camps),
        'total_pdf_files': len(all_camps),
        'camps': final_camps
    }

    with open('ecbt_camps.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'Done! {len(final_camps)} camps written to ecbt_camps.json')

if __name__ == '__main__':
    main()
