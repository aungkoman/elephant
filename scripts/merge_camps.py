"""
merge_camps.py
Merges the rich 001.json data into each individual slug-named camp JSON.
Run: python scripts/merge_camps.py
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMPS_DIR = ROOT / "site" / "src" / "content" / "camps"


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


# Load 001.json (rich array)
rich_file = CAMPS_DIR / "001.json"
raw = json.loads(rich_file.read_text(encoding="utf-8-sig"))
assert isinstance(raw, list), "001.json must be a JSON array"

# Build lookup keyed by normalized EN name
rich_by_name = {}
for c in raw:
    key = normalize(c.get("name", {}).get("en", ""))
    if key:
        rich_by_name[key] = c

slug_files = sorted(f for f in CAMPS_DIR.glob("*.json") if f.name != "001.json")
merged = 0
skipped = 0

for sf in slug_files:
    camp = json.loads(sf.read_text(encoding="utf-8"))

    # Find match in rich data
    key = normalize(camp.get("name_en", ""))
    rich = rich_by_name.get(key)

    # Fallback: partial prefix match
    if not rich and len(key) >= 5:
        for rk, rv in rich_by_name.items():
            if key[:5] in rk or rk[:5] in key:
                rich = rv
                break

    if not rich:
        print(f"  SKIP (no 001.json match): {camp.get('name_en')} -> {sf.name}")
        skipped += 1
        continue

    r_name   = rich.get("name", {})
    r_desc   = rich.get("description", {})
    r_price  = rich.get("pricing", {})
    r_svc    = rich.get("services", {})
    r_loc    = rich.get("location", {})
    r_coords = r_loc.get("coordinates", {})

    # --- Bilingual names
    camp["name_my"] = r_name.get("my") or camp.get("name_my")

    # --- Descriptions
    camp["description_en"] = r_desc.get("en") or camp.get("description_en")
    camp["description_my"] = r_desc.get("my") or camp.get("description_my")

    # --- Services
    camp["services_en"] = r_svc.get("en") or camp.get("services_en")
    camp["services_my"] = r_svc.get("my") or camp.get("services_my")

    # --- Location enrichment
    region_en = r_loc.get("region", {}).get("en", "")
    if not camp.get("region") and region_en:
        camp["region"] = region_en.split(",")[0].strip()
    camp["region_my"]  = r_loc.get("region", {}).get("my")
    camp["address_en"] = r_loc.get("address", {}).get("en")
    camp["address_my"] = r_loc.get("address", {}).get("my")

    # --- Coordinates: prefer 001.json when extracted value is a round fallback
    if r_coords.get("lat") and r_coords.get("long"):
        existing = camp.get("latitude")
        is_round = existing is not None and float(existing) == int(float(existing))
        if is_round or not existing:
            camp["latitude"]  = r_coords["lat"]
            camp["longitude"] = r_coords["long"]

    # --- Fees: fill in foreigner prices + update local if cleaner
    fees = camp.get("fees") or {}
    r_ent = r_price.get("entrance", {})
    if r_ent.get("local_mmk") is not None:
        fees["entrance_local_mmk"]     = r_ent["local_mmk"] or fees.get("entrance_local_mmk")
    if r_ent.get("foreign_mmk") is not None:
        fees["entrance_foreigner_mmk"] = r_ent["foreign_mmk"]

    for ride_key in ("riding", "riding_short"):
        r_ride = r_price.get(ride_key, {})
        if r_ride.get("local_mmk") is not None:
            fees["riding_local_mmk"]     = r_ride["local_mmk"] or fees.get("riding_local_mmk")
        if r_ride.get("foreign_mmk") is not None:
            fees["riding_foreigner_mmk"] = r_ride["foreign_mmk"]
    camp["fees"] = fees

    # Write merged file
    sf.write_text(json.dumps(camp, ensure_ascii=False, indent=2), encoding="utf-8")
    matched_name = r_name.get("en", "?")
    print(f"  OK  {sf.name:30s} <- {matched_name}")
    merged += 1

print(f"\nDone. {merged} merged, {skipped} skipped out of {len(slug_files)} camp files.")
