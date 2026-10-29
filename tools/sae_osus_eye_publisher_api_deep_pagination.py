#!/usr/bin/env python3
"""SAE existing Osus Eye: publisher-observed public API pagination, source-only.

Project identity mandatory: original id=5488221000080748758 and name OSUS EYE.
No inferred units from project marketing 627; only original coded sale cards.
"""
import hashlib,json,time,urllib.request,urllib.error,urllib.robotparser,re
from datetime import datetime,timezone
from urllib.parse import urlencode
from pathlib import Path
HOST="https://osus.com.sa"
PATH="/wp-json/osus/v1/properties"
PARAMS={"page_number":"1","page_size":"10","listing_type":"sale","lang":"en","sort":"created_at_desc"}
PROJECT_ID="5488221000080748758"
CANONICAL="PRJ-000336"
UA="SAE-DB-OsusEye-public-pagination-check/1.0"
O=Path("sae-osus-eye-exact-publisher-pagination-original.json")
data={"schema":"SAE_OSUS_EYE_FIRSTPARTY_PAGINATION_EXISTING_PROJECT_ONLY",
      "observed_utc":datetime.now(timezone.utc).isoformat(),
      "canonical_project":CANONICAL,"original_project_id":PROJECT_ID,
      "source_id":"SRC-000287","master_writes":0,
      "pages":[],"qualified_records":[],"errors":[]}
def save():
 O.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def check():
 with urllib.request.urlopen(urllib.request.Request(HOST+"/robots.txt",headers={"User-Agent":UA}),timeout=20) as r:
  if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
  raw=r.read(180000)
 rp=urllib.robotparser.RobotFileParser();rp.parse(raw.decode("utf8","replace").splitlines());return rp
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"}),timeout=35) as r:
  if r.status in (403,429):raise RuntimeError("STOP_HTTP_"+str(r.status))
  if r.status!=200:raise RuntimeError("HTTP_"+str(r.status))
  raw=r.read(3500000)
 if len(raw)>=3500000:raise RuntimeError("RESPONSE_TOO_LARGE")
 return raw
try:
 rp=check()
 seenids=set();seencodes=set();seenbody=set()
 for page in range(1,24):
  p={**PARAMS,"page_number":str(page)}
  url=HOST+PATH+"?"+urlencode(p)
  if not rp.can_fetch(UA,url):data["stop"]="ROBOTS_DENIED_API_"+str(page);break
  time.sleep(2.0)
  raw=fetch(url);sh=hashlib.sha256(raw).hexdigest()
  if sh in seenbody:
   data["stop"]="PUBLISHER_SAME_SOURCE_PAGE_HASH";break
  seenbody.add(sh)
  obj=json.loads(raw)
  rows=obj.get("data")
  if not isinstance(rows,list):data["stop"]="API_DATA_NOT_LIST";break
  receipt={"source_url":url,"page":page,"sha256":sh,"json_keys":list(obj)[:30],
           "pagination":{k:v for k,v in obj.items() if k not in ("data",) and isinstance(v,(int,str,bool,dict,list)) and len(str(v))<1500},
           "items":len(rows),"osus_eye_code_count":0,"other_project_codes":[]}
  if page==1:receipt["sample_item_keys"]=list(rows[0]) if rows else []
  for x in rows:
   if not isinstance(x,dict):continue
   code=x.get("unit_code");project=x.get("project") or {}
   if not isinstance(project,dict):continue
   pid=str(project.get("id") or "")
   if pid!=PROJECT_ID or project.get("name")!="OSUS EYE":
    receipt["other_project_codes"].append({"code":str(code)[:110],"project":project.get("name"),"publisherProjectId":pid})
    continue
   if not isinstance(code,str) or not re.fullmatch(r"OE/CL\d/[A-Z]\d/(?:GRD|\d(?:ST|ND|RD|TH))/[1-9]BR/\d+",code):
    data["errors"].append("UNMATCHED_EYE_CODE_"+str(code)[:70]);continue
   if x.get("listing_type")!="sale" or x.get("unit_type")!="Apartment" or x.get("id") is None:continue
   listed=str(x["id"])
   if listed in seenids or code in seencodes:
    data["errors"].append("SOURCE_DUPLICATE_IGNORED:"+str(listed));continue
   seenids.add(listed);seencodes.add(code)
   price=(x.get("pricing") or {}).get("price")
   row={"canonical_project_id":CANONICAL,"original_publisher_project_id":pid,
        "original_listing_id":listed,"original_unit_code":code,
        "firstparty_api_url":url,"original_unit_sale_url":HOST+"/en/sale/"+listed,
        "original_internal_unit_id":x.get("UnitId"),
        "pricing":price,"unit_type":x.get("unit_type"),
        "availability":x.get("availability"),
        "source_updated_at":x.get("updated_at"),
        "source_created_at":x.get("created_at"),
        "project_name":project.get("name")}
   receipt["osus_eye_code_count"]+=1
   data["qualified_records"].append(row)
  data["pages"].append(receipt)
  save()
  print("SAE_OSUS_EYE_PAGE",json.dumps({"page":page,"total_source_items":len(rows),
     "eye_count":receipt["osus_eye_code_count"],
     "other_projects":receipt["other_project_codes"][:4],
     "pagination":receipt["pagination"],
     "error_count":len(data["errors"])},ensure_ascii=False)[:2600],flush=True)
  if not rows or len(rows)<10:data["stop"]="API_LAST_SHORT_PAGE";break
 else:data["stop"]="MAX_23_PAGES_BOUND"
except Exception as exc:
 data["stop"]="FAIL_CLOSED_"+type(exc).__name__+":"+str(exc)[:190]
save()
print("SAE_OSUS_EYE_FINAL",json.dumps({"stop":data.get("stop"),"pages":len(data["pages"]),
 "source_eye_records":len(data["qualified_records"]),
 "unique_code":len({x["original_unit_code"] for x in data["qualified_records"]}),
 "errors":data["errors"][:8]},ensure_ascii=False),flush=True)
