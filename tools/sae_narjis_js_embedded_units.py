#!/usr/bin/env python3
"""Read-only discovery of original developer-linked Saraya Al Narjis map's embedded units.

Source is a public JS asset that the official Dar Wa Emaar project page links
to via its public interactive map. No login or internal URLs, and no Sheets
mutations. Extract only literal physical unit metadata from the original asset.
"""
import hashlib,json,re,urllib.request,urllib.robotparser
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

MAP_PAGE="https://digitalpartnersglobal.com/darwa/?lang=ar&view=riyadh"
JS_URL="https://digitalpartnersglobal.com/darwa/build/main.js?v51"
UA="SAE-DB-public-project-inventory-research/1.0"
EXPECTED_SOURCE_HASH="50be6bba96ec58355630edfe20a0de3e522df1cc62c99cd284fe1798b50d1877"
out={"schema":"SAE_SARAYA_NARJIS_ORIGINAL_PUBLIC_MAP_JS_PHYSICAL_UNIT_SOURCE_V1",
     "captured_utc":datetime.now(timezone.utc).isoformat(),
     "source_browser_page":MAP_PAGE,"source_original_js":JS_URL,
     "source_is_external_publisher_map_linked_from_developer":True,
     "expected_sha256":EXPECTED_SOURCE_HASH,"records":[],"hold":[],"sheets_mutations":0}
def numeric(txt,field):
    m=re.search(r"(?<![a-zA-Z])"+re.escape(field)+r":(-?\d+(?:\.\d+)?)",txt)
    return float(m[1]) if m and "." in m[1] else int(m[1]) if m else None
try:
    with urllib.request.urlopen(urllib.request.Request(
          "https://digitalpartnersglobal.com/robots.txt",headers={"User-Agent":UA}),timeout=15) as r:
        if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
        rp=urllib.robotparser.RobotFileParser()
        rp.parse(r.read(200000).decode("utf-8","replace").splitlines())
    if not rp.can_fetch(UA,JS_URL):raise RuntimeError("ROBOTS_DENY_JS")
    with urllib.request.urlopen(urllib.request.Request(JS_URL,headers={"User-Agent":UA}),timeout=30) as r:
        out["source_status"]=r.status
        if r.status in (403,429):raise RuntimeError("STOP_ACCESS_"+str(r.status))
        body=r.read(7000000)
    out["source_size"]=len(body);out["source_sha256"]=hashlib.sha256(body).hexdigest()
    if out["source_sha256"]!=EXPECTED_SOURCE_HASH:
        raise RuntimeError("SOURCE_HASH_CHANGED_MANUAL_REVIEW_REQUIRED")
    source=body.decode("utf-8","replace")
    out["landNumber_field_mentions"]=source.count("landNumber:")
    start_re=re.compile(r'"(?P<code>\d{2}_\d{2}_\d{1,4})":\{blockNumber:"(?P<block>[^"]{3,20})",landNumber:(?P<unitno>\d+)')
    matches=list(start_re.finditer(source))
    out["source_pattern_matches"]=len(matches)
    for m in matches:
        closing=source.find("}",m.end())
        if closing<0 or closing-m.start()>1500:
            out["hold"].append({"source_key":m.group("code"),"reason":"RECORD_NOT_CLOSED_IN_LIMIT"})
            continue
        text=source[m.start():closing+1]
        key=m.group("code");block=m.group("block");land=int(m.group("unitno"))
        if key[:5].replace("_","-")!=block or int(key[6:])!=land:
            out["hold"].append({"source_key":key,"reason":"KEY_BLOCK_LANDNUMBER_MISMATCH","block":block,"landNumber":land})
            continue
        model=re.search(r'model:"([^"]{1,30})"',text)
        floor=re.search(r'floor:\[([^\]]{0,200})\]',text)
        avail=re.search(r'available:(![01]|true|false)',text)
        row={"publisher_unit_code":key,"original_block_number":block,"original_land_number":land,
             "cluster":numeric(text,"cluster"),"model":model[1] if model else None,
             "land_area_sqm":numeric(text,"landArea"),"house_area_sqm":numeric(text,"houseArea"),
             "rooms":numeric(text,"rooms"),
             "floor_labels":re.findall(r'"([^"]+)"',floor[1]) if floor else None,
             "original_availability_literal":avail[1] if avail else None,
             "source_text_offset":m.start()}
        out["records"].append(row)
    counts=Counter(r["publisher_unit_code"] for r in out["records"])
    out["duplicate_keys"]=[k for k,v in counts.items() if v>1][:150]
    out["unit_count_total"]=len(out["records"])
    out["distinct_exact_original_unit_codes"]=len(counts)
    out["records_with_positive_area"]=sum((r["land_area_sqm"] or 0)>0 for r in out["records"])
    out["records_with_positive_house_area"]=sum((r["house_area_sqm"] or 0)>0 for r in out["records"])
    out["original_availability_literals"]=dict(Counter(r["original_availability_literal"] for r in out["records"]))
    out["cluster_distribution"]=dict(Counter(str(r["cluster"]) for r in out["records"]))
    out["model_distribution"]=dict(Counter(str(r["model"]) for r in out["records"]))
    out["count_without_required_code_identity"]=len(out["hold"])
    out["status"]="SOURCE_ONLY_EXACT_JS_RECORDS_FOR_CANONICAL_PROJECT_AND_DUPLICATE_QA"
except Exception as e:
    out["status"]="STOP_NO_SOURCE_PROMOTION"
    out["error"]=str(e)[:280]
Path("sae-narjis-original-js-coded-units.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:out.get(k) for k in (
    "status","source_sha256","landNumber_field_mentions","source_pattern_matches",
    "unit_count_total","distinct_exact_original_unit_codes",
    "duplicate_keys","count_without_required_code_identity","model_distribution",
    "cluster_distribution","error")},ensure_ascii=False))
