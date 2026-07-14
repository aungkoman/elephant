"""
extract_camps.py  —  Extracts structured data from ECBT camp PDFs
Usage:  python scripts/extract_camps.py
Req:    pip install pymupdf
"""
import fitz, json, os, re, unicodedata
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
OUT_DIR  = ROOT / "site" / "src" / "content" / "camps"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Slug helper
def slugify(text):
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", "-", text)   # CamelCase → camel-Case
    text = text.lower()
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"[^a-z0-9-]", "", text)

# ── PDF text
def extract_text(pdf_path):
    doc = fitz.open(str(pdf_path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)

def contains_myanmar(text):
    return bool(re.search(r"[\u1000-\u109F]", text))

# ── Parsers
def parse_lat_lon(text):
    def dms_to_dd(parts):
        d = float(parts[0]) if len(parts) > 0 else 0
        m = float(parts[1]) if len(parts) > 1 else 0
        s = float(parts[2]) if len(parts) > 2 else 0
        return round(d + m/60 + s/3600, 6)
    lat_m = re.search(r"Latitude\s*\(?[N]?\)?\s*[-:()\s]*([0-9.]+)[°\s]*([0-9.]*)['\s]*([0-9.]*)[\"\s]*[N]?", text, re.I)
    lon_m = re.search(r"Longitude\s*\(?[E]?\)?\s*[-:()\s]*([0-9.]+)[°\s]*([0-9.]*)['\s]*([0-9.]*)[\"\s]*[E]?", text, re.I)
    lat = dms_to_dd([g for g in lat_m.groups() if g]) if lat_m else None
    lon = dms_to_dd([g for g in lon_m.groups() if g]) if lon_m else None
    return lat, lon

def parse_hours(text):
    m = re.search(r"Opening hours?\s*[-–:]+\s*(.+?)(?:\n|$)", text, re.I)
    return m.group(1).strip() if m else None

def parse_fees(text):
    def mmk(pattern):
        m = re.search(pattern, text, re.I | re.S)
        return int(m.group(1).replace(",","")) if m else None
    return {
        "entrance_local_mmk":     mmk(r"Entrance fee.*?Local.*?-\s*([\d,]+)\s*MMK"),
        "entrance_foreigner_mmk": mmk(r"Entrance fee.*?Foreigner.*?-\s*([\d,]+)\s*MMK"),
        "riding_local_mmk":       mmk(r"Elephant Riding fee.*?-\s*([\d,]+)\s*MMK"),
        "riding_foreigner_mmk":   mmk(r"Elephant Riding fee.*?Foreigner.*?-\s*([\d,]+)\s*MMK"),
    }

ACTIVITIES = [
    "Elephant Riding","Elephant Bathing","Elephant Show","Elephant Feeding",
    "Elephant Buffet","Photography","Video Recording","Jungle Walk","Trekking",
    "Boat","Rafting","Wedding","Pre Wedding","Conservation","Souvenir","Restaurant","Relax",
]
def parse_activities(text):
    return [a for a in ACTIVITIES if re.search(re.escape(a), text, re.I)]

def parse_contacts(text):
    phones = re.findall(r"\b0[\d\s\-]{7,12}", text)
    seen, out = set(), []
    for p in phones:
        p = re.sub(r"[\s\-]", "", p).strip()
        if 8 <= len(p) <= 12 and p not in seen:
            seen.add(p); out.append(p)
    return out

def parse_facebook(text):
    m = re.search(r"(https?://(?:www\.)?facebook\.com/\S+)", text)
    return m.group(1).rstrip(".,\n") if m else None

def parse_elephants(text):
    total = re.search(r"(\d+)\s+(?:male\s+and\s+\d+\s+female|female\s+and\s+\d+\s+male|\w+\s+)?elephant", text, re.I)
    male  = re.search(r"(\d+)\s+[Mm]ale", text)
    fem   = re.search(r"(\d+)\s+[Ff]emale", text)
    return {
        "total":  int(total.group(1)) if total else None,
        "male":   int(male.group(1))  if male  else None,
        "female": int(fem.group(1))   if fem   else None,
    }

def parse_area(text):
    m = re.search(r"Camp Area\s*[-–:]\s*(.+?)(?:\n|Acre)", text, re.I)
    if m: return m.group(1).strip() + " Acres"
    m = re.search(r"([\d.,]+\s*Acres?)", text, re.I)
    return m.group(1) if m else None

REGION_MAP = {
    "Bago":"Bago","Yangon":"Yangon","Mandalay":"Mandalay","Naypyitaw":"Naypyitaw",
    "Nay Pyi Taw":"Naypyitaw","Pathein":"Ayeyarwady","Ngwe Saung":"Ayeyarwady",
    "Pyay":"Bago","Taunggyi":"Shan","Taungngu":"Bago","Ngapali":"Rakhine",
    "Nyaung Oo":"Mandalay","Bagan":"Mandalay","Minhla":"Magway","Kalaw":"Shan",
    "Pyin Oo Lwin":"Mandalay",
}
def parse_region(text, dir_name):
    for keyword, region in REGION_MAP.items():
        if keyword.lower() in text.lower() or keyword.lower() in dir_name.lower():
            return region
    return None

NAME_MAP = {
    "1000Bodhi":      "1000 Bodhi Elephant Conservation Camp",
    "HmawYawGyi":     "Hmaw Yaw Gyi Elephant Conservation Camp",
    "KhaiKam":        "Khai Kam Elephant Camp",
    "KyunTaw":        "Kyun Taw Elephant Conservation Camp",
    "Moemaka":        "Moe Ma Kha Elephant Camp",
    "Mokka":          "Mokkha Waterfall Elephant Conservation Camp",
    "MyaingHayWon":   "Myaing Hay Won Elephant Conservation Camp",
    "NatHmaw":        "Nat Hmaw Elephant Conservation Camp",
    "NayPyiTaw":      "Royal White Elephants Conservation Garden",
    "NgaLaik":        "Ngalaik Sa Khan Thar Elephant Conservation Camp",
    "NgweSaung":      "Ngwe Saung Elephant Conservation Camp",
    "Palin":          "Palin Elephant Camp",
    "PhoeKyar":       "Phoe Kyar Elephant Camp",
    "PyarSwal":       "Pyar Swal Elephant Camp",
    "SarniTaung":     "Sarni Taung Elephant Conservation Camp",
    "Serikestra":     "Srikestra Elephant Conservation Camp",
    "ShanYoma":       "Shan Yoma Elephant Camp",
    "ShweSetTaw":     "Shwe Set Taw Elephant Camp",
    "Wanet":          "Wanet Elephant Conservation Camp",
    "Wingabaw":       "Wingabaw Elephant Conservation Camp",
}

def process_camp(camp_dir):
    key = camp_dir.name.split("_")[0]
    slug = slugify(key)
    en_text, my_text = "", ""
    for pdf in sorted(camp_dir.glob("*.pdf")):
        t = extract_text(pdf)
        nl = pdf.name.lower()
        if "myanmar" in nl and "english" not in nl:
            my_text = t
        else:
            en_text = t
            if not my_text and contains_myanmar(t): my_text = t

    combined = en_text or my_text
    lat, lon = parse_lat_lon(combined)

    return {
        "slug":        slug,
        "name_en":     NAME_MAP.get(key, key),
        "name_my":     None,
        "region":      parse_region(combined, camp_dir.name),
        "ministry":    "Ministry of Natural Resources and Environmental Conservation"
                       if "Ministry" in combined else None,
        "latitude":    lat,
        "longitude":   lon,
        "area":        parse_area(combined),
        "elephants":   parse_elephants(combined),
        "hours":       parse_hours(combined),
        "fees":        parse_fees(combined),
        "activities":  parse_activities(combined),
        "contacts":    parse_contacts(combined),
        "facebook":    parse_facebook(combined),
        "source_dir":  camp_dir.name,
        "has_en_pdf":  bool(en_text),
        "has_my_pdf":  bool(my_text),
    }

def main():
    dirs = sorted(d for d in DOCS_DIR.iterdir() if d.is_dir())
    print(f"Processing {len(dirs)} camps...")
    for d in dirs:
        print(f"  {d.name}", end=" ... ")
        data = process_camp(d)
        out = OUT_DIR / f"{data['slug']}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK -> {out.name}")
    print(f"\nDone. {len(dirs)} JSON files in {OUT_DIR}")

if __name__ == "__main__":
    main()
