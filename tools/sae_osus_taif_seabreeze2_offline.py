#!/usr/bin/env python3
"""Parse two fully captured ORIGINAL Osus public unit grids offline.
Only existing PRJ-001138 and PRJ-000774. Never infer codes or offer states.
"""
import json,re,hashlib,unicodedata
from pathlib import Path
IN=Path("sae-osus-taif-seabreeze2-firstparty-grid.json")
OUT=Path("sae-osus-taif-seabreeze2-171-source-cards.json")
EXPECTED={"PRJ-001138":63,"PRJ-000774":108}
VALID_STATUS={"متاحة","مباعة","محجوزة"}
AR_NUMS=str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹","01234567890123456789")
def parse_number(raw, whole=False, allow_zero=False):
    s=str(raw).translate(AR_NUMS).replace("٬","").replace(",","").replace("٫",".").replace(" ","")
    s=re.sub(r"[^0-9.]","",s)
    if not s or s.count(".")>1:raise ValueError("invalid source number "+repr(raw))
    value=float(s)
    if value<0 or (value==0 and not allow_zero):raise ValueError("nonpositive number")
    if whole and value!=int(value):raise ValueError("noninteger source field")
    return int(value) if whole else value
def extract_one(item):
    pid=item["project_id"]
    if pid not in EXPECTED:raise ValueError("outside existing canonical project")
    if not item.get("allowed") or item.get("http")!=200 or item.get("blocked") or item.get("errors"):
        raise ValueError("source cannot be qualified due to access/errors: "+pid)
    if item["final_structure"]["headings"]!=EXPECTED[pid]:
        raise ValueError("not all public headings captured: "+pid)
    text=item["final_text"]
    if "الوحدات المتاحة" not in text or "إجمالي الوحدات" not in text:raise ValueError("missing source inventory boundary")
    body=text.split("الوحدات المتاحة",1)[1].split("إجمالي الوحدات",1)[0]
    lines=[s.strip() for s in body.splitlines() if s.strip()]
    records=[];building=None;seen=set()
    def field(block,prefix):
        for j,p in enumerate(block):
            if p.startswith(prefix) and ":" in p:
                val=p.split(":",1)[1].strip()
                return val or (block[j+1] if j+1<len(block) else None)
        return None
    for i,line in enumerate(lines):
        mb=re.fullmatch(r"المبنى\s+(.+)",line)
        if mb:
            building=mb.group(1).strip().translate(AR_NUMS)
        mu=re.fullmatch(r"الوحدة\s+([\w\-]+)",line)
        if not mu:continue
        code=mu.group(1).strip().translate(AR_NUMS)
        if not building:raise ValueError(f"unit has no building: {pid}/{code}")
        end=i+1
        while end<len(lines) and not (lines[end].startswith("الوحدة ") or lines[end].startswith("المبنى ") or lines[end]=="إجمالي الوحدات"):
            end+=1
        block=lines[i+1:end]
        status=next((s for s in block if s in VALID_STATUS),None)
        price_idx=next((j for j,s in enumerate(block) if s.strip().rstrip(":")=="السعر"),None)
        price=block[price_idx+1] if price_idx is not None and price_idx+1<len(block) else None
        room=field(block,"الغرف")
        floor=field(block,"الطابق")
        area=field(block,"المساحة الإجمالية")
        private_area=field(block,"المساحة الخاصة")
        if status is None or area is None or price is None:
            raise ValueError("missing source card data "+repr((pid,building,code,block[:20])))
        key=(building,code)
        if key in seen:raise ValueError("duplicated physical code in building "+repr((pid,key)))
        seen.add(key)
        rec={"canonical_project_id":pid,"publisher_unit_code":code,
            "publisher_building_no":building,
            "status_original_ar":status,"price_sar":parse_number(price,True),
            "bedrooms":parse_number(room,True) if room is not None else None,"floor":parse_number(floor,True) if floor is not None else None,
            "area_sqm":parse_number(area,False),
            "publisher_private_area_sqm":parse_number(private_area,False,True) if private_area else None,
            "source_url":item["original_url"],"source_capture_utc":item["capture_utc"],
            "source_card_excerpt":block[:14]}
        records.append(rec)
    if len(records)!=EXPECTED[pid]:
        print("DIAGNOSTIC_FIRST_3500",pid,body[:3500],flush=True)
        print("DIAGNOSTIC_FOUND",len(records),len(seen),flush=True)
        raise ValueError(f"itemized source records count mismatch {pid}: {len(records)} != {EXPECTED[pid]}")
    return records
def main():
    raw=IN.read_bytes()
    data=json.loads(raw)
    results=[]
    for x in data["rows"]:
        rows=extract_one(x)
        print("QUALIFIED",x["project_id"],"cards",len(rows),"source_sha256",hashlib.sha256(x["final_text"].encode()).hexdigest(),flush=True)
        results.extend(rows)
    for q in results:
        if q["area_sqm"] < 50 or q["area_sqm"] > 350:
            print("SAE_SOURCE_AREA_HOLD|"+json.dumps(q,ensure_ascii=False,separators=(",",":")),flush=True)
    if len(results)!=171:raise ValueError("source cards not exactly 171")
    output={"schema":"SAE_DB_OSUS_TAIF_SEABREEZE2_171_SOURCE_ORIGINAL_CARDS_STAGED_ONLY",
        "source_capture_artifact_sha256":hashlib.sha256(raw).hexdigest(),
        "imported_master_units":0,"records":results}
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for row in results:
        flat={k:v for k,v in row.items() if k!="source_card_excerpt"}
        print("SAE_OSUS_ROW|"+json.dumps(flat,ensure_ascii=False,separators=(",",":")),flush=True)
    print("FINISHED_STAGED_ONLY",len(results),flush=True)
if __name__=="__main__":main()
