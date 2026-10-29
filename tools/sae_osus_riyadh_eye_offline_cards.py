#!/usr/bin/env python3
"""Validate 9 first-party OSUS Eye physical sale cards against original API, no Sheets writes."""
import json,re,hashlib
from pathlib import Path
SRC=Path("sae-osus-riyadh-original-unit-inventory.json")
OUT=Path("sae-osus-eye-nine-verified-original-sale-cards.json")
o=json.loads(SRC.read_text())
body=o.get("final_body","")
links={a["text"]:a["href"] for a in o.get("final_links",[]) if a.get("text","").startswith("OE/")}
apis=[r for r in o.get("responses",[]) if "/wp-json/osus/v1/properties?" in r.get("url","")]
if o.get("http")!=200 or o.get("blocked") or len(apis)!=1:raise ValueError("original browser publisher access or API not exact")
api=apis[0]
source=json.loads(api["original_response_excerpt"])
rows=source.get("data")
if not isinstance(rows,list) or len(rows)!=9 or len(links)!=9:raise ValueError("original nine card list inconsistency")
pattern=re.compile(r"(OE/CL\d/[A-Z]\d/(?:GRD|\d(?:ST|ND|RD|TH))/[1-9]BR/\d+)\s+OSUS EYE\s+An Nada\s+([0-9.]+) sqm\s+(\d+) Beds\s+(\d+) Bath\s+([0-9,.]+)\s+View More Details")
cards={m.group(1):{"area_sqm":float(m.group(2)),"bedrooms":int(m.group(3)),"bathrooms":int(m.group(4)),"displayed_asking_price_sar":float(m.group(5).replace(",",""))} for m in pattern.finditer(body)}
if len(cards)!=9:raise ValueError("visible original source listing card parsing mismatch")
verified=[];seen=set()
for x in rows:
 code=x.get("unit_code","")
 if code in seen or code not in links or code not in cards or x.get("project",{}).get("name")!="OSUS EYE":raise ValueError("source code project or link mismatch "+code)
 seen.add(code)
 sale="https://osus.com.sa/en/sale/"+str(x.get("id"))
 if links[code]!=sale:raise ValueError("publisher original listing id and URL mismatch "+code)
 if x.get("listing_type")!="sale" or x.get("unit_type")!="Apartment":raise ValueError("source listing type not accepted")
 price=float(x["pricing"]["price"])
 if abs(price-cards[code]["displayed_asking_price_sar"])>0.001:raise ValueError("publisher published price and display mismatch "+code)
 if price<=0 or not bool(x.get("availability")):raise ValueError("source sale availability not positive "+code)
 parts=code.split("/")
 if len(parts)!=6:raise ValueError("original code malformed")
 verified.append({"project_id":"PRJ-000336","project_name":"عين أسس Osus Eye","original_publisher_unit_code":code,
    "original_publisher_listing_id":str(x["id"]),"original_publisher_internal_unit_id":x.get("UnitId"),
    "original_project_publisher_id":str(x["project"]["id"]),"original_sale_url":sale,
    "original_source_listing_url":o["source_page"],"original_api_url":api["url"],
    "original_building_cluster":parts[1],"original_building_code":parts[2],
    "original_floor":parts[3],"original_bedrooms_from_code":int(parts[4].replace("BR","")),
    "original_ordinal":parts[5],
    "publisher_unit_type":x["unit_type"],"publisher_available":x["availability"],
    "source_created_at":x.get("created_at"),"source_updated_at":x.get("updated_at"),
    "capture_utc":o["utc"],"price_sar":price,
    "area_sqm":cards[code]["area_sqm"],"bedrooms":cards[code]["bedrooms"],
    "bathrooms":cards[code]["bathrooms"],"source_public_asking_currency":"SAR"})
 if verified[-1]["bedrooms"]!=verified[-1]["original_bedrooms_from_code"]:raise ValueError("code versus published bedrooms mismatch")
if len(verified)!=9:raise ValueError("wrong count")
res={"schema":"SAE_OSUS_EYE_RIYADH_NINE_ORIGINAL_INDIVIDUAL_PHYSICAL_SALE_UNITS_V1",
     "source_only":True,"publisher_domain":"osus.com.sa","NOT_SAME_PUBLISHER_AS_osuse.sa":True,
     "master_rows_written":0,"source_capture_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
     "api_sha256":api["sha256"],"original_public_api_url":api["url"],
     "record_count":len(verified),"records":verified}
OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
print("SAE_EYE_FIELD_KEYS",json.dumps({"top":list(rows[0]),"project":list(rows[0].get("project",{})),"api_top":list(source)},ensure_ascii=False))
for z in verified:print("SAE_EYE_VERIFIED_ROW|"+json.dumps(z,ensure_ascii=False,separators=(",",":")),flush=True)
print("SAE_EYE_NORMALIZED_9_PASS",len(verified),flush=True)
