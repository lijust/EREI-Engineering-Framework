#!/usr/bin/env python3
"""Deterministic site-intelligence evidence gate for original physical units.

Not an LLM guesser. Distinguishes marketing totals, maps widgets, table controls,
API response shapes and evidenced developer-coded individual physical units.
Zero canonical writes and no assumption of legal availability.
"""
from __future__ import annotations
import json, re
from urllib.parse import urlsplit

UNIT_KEYS={"unitCode","unit_code","unitNumber","unit_number","doorNumber",
           "door_number","villaNumber","villa_number","plotNumber","plot_number"}
PROJECT_KEYS={"projectId","project_id","projectNumber","project_number"}
BUILDING_KEYS={"propertyId","property_id","buildingId","building_id","buildingNumber","building_number"}
DETAIL_KEYS={"area","totalArea","area_sqm","price","salePrice","bedrooms","bathrooms","floor"}
BAD_HOSTS={"google.com","googleapis.com","google-analytics.com","doubleclick.net"}
BAD_PATHS=("/api/public/google-tags/", "/g/collect", "/mapsjs/", "/$rpc/")
BAD_TABLE_HEADINGS={("keystroke","action"),("keyboard shortcut","action"),
                    ("key","action"),("shortcut","action")}

def _bad_url(url:str)->bool:
    try:parsed=urlsplit(url)
    except ValueError:return True
    host=(parsed.hostname or "").lower()
    path=parsed.path.lower()
    return any(host==h or host.endswith("."+h) for h in BAD_HOSTS) or any(x in path for x in BAD_PATHS)

def classify_table(headers, rows):
    """Never treat row count alone as individually published units."""
    normalized=tuple(" ".join(str(c).lower().split()) for r in headers for c in r)
    if normalized in BAD_TABLE_HEADINGS:
        return {"class":"NON_PROPERTY_ACCESSIBILITY_TABLE","accepted":0,"reason":"Keyboard shortcuts / map controls"}
    if not headers:
        return {"class":"TABLE_UNCLASSIFIED","accepted":0,"reason":"No headers or identity evidence"}
    words=" ".join(normalized)
    has_unit=bool(re.search(r"unit.?number|unit.?code|villa.?number|plot.?number|رقم.?الوحدة|رقم.?الفيلا|رقم.?القطعة", words))
    has_project=bool(re.search(r"project|building|العمارة|المبنى|المشروع|المخطط", words))
    if not (has_unit and has_project):
        return {"class":"TABLE_NEEDS_IDENTITY_FIELDS","accepted":0,"reason":"No source unit+parent/building identity headers"}
    return {"class":"POTENTIAL_ITEMIZED_TABLE_REQUIRES_ROW_VERIFICATION","accepted":0,"source_rows":len(rows),
            "reason":"Individual IDs not yet validated; no canonical write"}

def classify_xhr_endpoint(item):
    """Require original unit+parent keys in the same JSON array, never generic shapes."""
    url=item.get("url","")
    if _bad_url(url):
        return {"class":"THIRD_PARTY_OR_TELEMETRY_EXCLUDED","accepted":0}
    shapes=item.get("shape") or []
    candidates=[]
    for shape in shapes:
        fields=set(shape.get("first_item_fields",[])+shape.get("visible_field_names",[]))
        if (fields & UNIT_KEYS) and (fields & (PROJECT_KEYS | BUILDING_KEYS)):
            candidates.append({"path":shape.get("path"),"fields":sorted(fields)})
    if not candidates:
        return {"class":"NO_SOURCE_UNIT_IDENTITY_IN_XHR_SHAPES","accepted":0}
    return {"class":"CANDIDATE_FIRSTPARTY_UNIT_API_NEEDS_ITEM_VALIDATION","accepted":0,
            "candidate_paths":candidates}

def inspect_report(report):
    results=[]
    for site in report.get("sites",[]):
        body={"key":site.get("key"),"source_url":site.get("url"),
              "status":"NO_CONFIRMED_INDIVIDUAL_SOURCE",
              "validated_new_physical_units":0,
              "xhr_candidates":[],"source_links_only":site.get("static",{}).get("public_links",[])}
        b=site.get("browser",{})
        for item in b.get("xhr",[]):
            check=classify_xhr_endpoint(item)
            if check["class"]=="CANDIDATE_FIRSTPARTY_UNIT_API_NEEDS_ITEM_VALIDATION":
                body["xhr_candidates"].append({"source_url":item.get("url"),"check":check})
        if body["xhr_candidates"]:
            body["status"]="PROVISIONAL_ENDPOINTS_ONLY_VALIDATE_ROWS_AND_EXISTING_PROJECT"
        body["marketing_project_total_not_unit_count"]=site.get("published_aggregate_not_individual")
        results.append(body)
    return {"schema":"SAE_SOURCE_INTELLIGENCE_EVIDENCE_GATE_V1","sites":results,
            "new_units_committed":0,"source_assumptions_banned":True}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("report")
    p.add_argument("--out",default=None)
    args=p.parse_args()
    with open(args.report,encoding="utf8") as f:obj=json.load(f)
    r=inspect_report(obj)
    rendered=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
    if args.out:
        with open(args.out,"w",encoding="utf8") as f:f.write(rendered)
    print(rendered)
