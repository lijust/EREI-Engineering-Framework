#!/usr/bin/env python3
"""Public firstparty Almajdiah projects API bulk pagination. No SAE private mappings or customer data."""
import json,os,sys,time,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,urljoin
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
UA="SAE-DB-public-realestate-source-units/1.0"
HOST="etmaam.almajdiah.com"
GROUPS={
"g1":{"229":"الماجدية 174","234":"الماجدية 178","239":"الماجدية 183","248":"الماجدية 192"},
"g2":{"232":"خيالا","221":"المشرقية 2"},
"g3":{"203":"جزيل","210":"مكانة","218":"فلل رِفان","241":"أديم الفرسان"},
"g4":{"180":"دروازة","236":"فلل البساتين","190":"سدو","186":"مشراف الماجدية"}
}
group=sys.argv[1] if len(sys.argv)>1 else ""
if group not in GROUPS:raise SystemExit("Need g1,g2,g3,g4")
OUT=Path(os.environ["RUNNER_TEMP"])/("almajdiah_firstparty_"+group+"_source_cards.json")
state={"schema":"PUBLIC_ALMAJDIAH_API_PER_UNIT_PAGINATED_V2","group":group,"status":"STARTED",
 "projects":[],"cards":[],"errors":[],"private_master_mapping_used":False,"production_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def get(url,api_id=None):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or p.port or p.username or p.password:raise ValueError("INVALID_SOURCE_HOST")
 if api_id is None:
  if p.path!="/robots.txt" or p.query:raise ValueError("INVALID_ROBOTS_PATH")
 else:
  if p.path!="/api/client/v1/projects/"+str(api_id):raise ValueError("API_SOURCE_PATH_CHANGED")
  qs=parse_qs(p.query)
  if any(k not in ("page","per_page") for k in qs):raise ValueError("API_UNEXPECTED_QUERY")
  if any(not all(re.fullmatch(r"[0-9]{1,4}",v) for v in vs) for vs in qs.values()):raise ValueError("BAD_API_QUERY_VALUES")
 r=Fetcher.get(url,retries=1,timeout=35,follow_redirects="safe",headers={"User-Agent":UA,"Accept":"application/json"})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_HALT")
 target=urlsplit(str(r.url))
 if target.hostname!=HOST or target.path!=p.path:raise ValueError("API_REDIRECTED_OFF_SCOPE")
 if int(r.status)!=200:raise RuntimeError("PUBLISHER_HTTP_"+str(r.status))
 return json.loads(r.body)
try:
 r=get("https://"+HOST+"/robots.txt")
 # Fetcher response of robots cannot be JSON; use the same exact restricted host request here.
except Exception:
 r=None
try:
 rb=Fetcher.get("https://"+HOST+"/robots.txt",retries=1,timeout=30,follow_redirects="safe",headers={"User-Agent":UA})
 if int(rb.status)==429:raise RuntimeError("HTTP_429_GLOBAL_HALT")
 if int(rb.status)!=200:raise RuntimeError("ROBOTS_HTTP_"+str(rb.status))
 if urlsplit(str(rb.url)).hostname!=HOST:raise ValueError("ROBOTS_REDIRECT")
 rp=RobotFileParser();rp.parse(rb.body.decode("utf-8","replace").splitlines())
 seen_ids=set();seen_codes=set()
 for pid,expected_name in GROUPS[group].items():
  first="https://"+HOST+"/api/client/v1/projects/"+pid
  url=first;pages=0;count=0;origin_status={};seen_urls=set()
  while url and pages<40:
   if url in seen_urls:raise ValueError("REPEATED_PAGINATION_"+pid)
   seen_urls.add(url)
   if not rp.can_fetch(UA,url):raise ValueError("ROBOTS_DISALLOW_"+pid)
   time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
   body=get(url,pid);project=body.get("project")
   if not isinstance(project,dict) or str(project.get("id"))!=pid or str(project.get("name"))!=expected_name:
    raise ValueError("OFFICIAL_PROJECT_IDENTITY_MISMATCH_"+pid+"_"+str(project.get("name") if isinstance(project,dict) else "none"))
   grouped=body.get("units")
   if grouped is None:
    if pages:raise ValueError("UNITS_DISAPPEARED_MID_PAGINATION_"+pid)
    break
   if not isinstance(grouped,dict) or not isinstance(grouped.get("data"),list):raise ValueError("UNKNOWN_UNIT_API_SHAPE_"+pid)
   for x in grouped["data"]:
    if not isinstance(x,dict) or not isinstance(x.get("id"),int) or not str(x.get("unit_number") or ""):raise ValueError("UNIT_SOURCE_ID_ABSENT")
    sid=pid+"|"+str(x["id"])
    code=pid+"|"+str(x.get("building_name") or "")+"|"+str(x.get("unit_number") or "")
    if sid in seen_ids or code in seen_codes:raise ValueError("DUPLICATE_PUBLISHER_SOURCE_UNIT_"+sid)
    seen_ids.add(sid);seen_codes.add(code)
    attrs=("id","building_name","unit_number","floor","floor_text","room_count","bathroom_count","area","total_area","special_area",
    "price_before_tax","price_after_tax","tax_value","status","status_text","sale_type","available_for_rent")
    safe={k:x.get(k) for k in attrs}
    safe["publisher_project_id"]=pid;safe["original_project_name"]=expected_name;safe["source_url"]=first;safe["source_page_url"]=url
    state["cards"].append(safe)
    status=str(x.get("status") or "NULL");origin_status[status]=origin_status.get(status,0)+1
    count+=1
   pages+=1
   save()
   next_url=(grouped.get("links") or {}).get("next")
   if next_url:
    if not isinstance(next_url,str):raise ValueError("NON_URL_NEXT")
    next_url=urljoin(url,next_url)
    get_host=urlsplit(next_url)
    if get_host.hostname!=HOST or get_host.path!=urlsplit(first).path:raise ValueError("OFF_SCOPE_NEXT_PAGE")
   url=next_url
   print("PAGE_SOURCE_PROGRESS "+json.dumps({"group":group,"project":pid,"page":pages,"seen":count},separators=(",",":")))
  if url:raise RuntimeError("PAGINATION_LIMIT_40_"+pid)
  project_state={"id":pid,"name":expected_name,"official_itemized_cards":count,"pages":pages,"marketing_total":project.get("units_count"),"published_statuses":origin_status}
  state["projects"].append(project_state);save()
  print("ORIGINAL_PROJECT_COMPLETE "+json.dumps(project_state,ensure_ascii=False,separators=(",",":")))
 state["status"]="COMPLETE_ALL_FIRSTPARTY_PROJECT_PAGES"
except Exception as exc:
 state["status"]="STOPPED_429" if "HTTP_429_GLOBAL_HALT" in str(exc) else "STOPPED_ERROR"
 state["errors"].append({"error":type(exc).__name__+": "+str(exc)[:240]})
finally:
 save()
 print("ALMAJDIAH_BULK_GROUP_SUMMARY "+json.dumps({"group":group,"status":state["status"],"projects":state["projects"],"cards":len(state["cards"]),"errors":state["errors"]},ensure_ascii=False,separators=(",",":")))
 for idx in range(0,len(state["cards"]),12):
  print("ALMAJDIAH_BULK_CARDS_JSON "+json.dumps(state["cards"][idx:idx+12],ensure_ascii=False,separators=(",",":")))
if state["status"]!="COMPLETE_ALL_FIRSTPARTY_PROJECT_PAGES":raise SystemExit(1)
