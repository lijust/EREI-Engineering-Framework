#!/usr/bin/env python3
"""Robots-gated original Asas Makeen 63 and 66 individual published unit cards."""
import json,os,time,re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LX
HOST="asasmakeen.com"
URLS={"63":"https://asasmakeen.com/ar/u/pu/3/42/%D8%B4%D9%82%D9%82-%D8%AD%D9%8A-%D8%A7%D9%84%D8%B9%D8%A7%D8%B1%D8%B6-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6-%D9%85%D9%83%D9%8A%D9%86-63",
"66":"https://asasmakeen.com/ar/u/pu/3/45/%D8%B4%D9%82%D9%82-%D8%AD%D9%8A-%D8%A7%D9%84%D8%B1%D9%85%D8%A7%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9"}
UA="SAE-DB-public-original-firstparty-unit-cards/1.0"
OUT=Path(os.environ["RUNNER_TEMP"])/"makeen63_66_firstparty_issued_unit_cards.json"
state={"schema":"FIRSTPARTY_MAKEEN63_66_ITEMIZED_UNIT_CARDS_V1","status":"STARTED",
 "pages":[],"cards":[],"errors":[],"private_canonical_ids":False,"writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def txt(el):return " ".join(" ".join(el.itertext()).split()) if el is not None else ""
def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or (p.path!="/robots.txt" and not p.path.startswith("/ar/u/pu/3/")):
  raise ValueError("OFF_SOURCE_URL")
 r=Fetcher.get(url,retries=1,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if urlsplit(str(r.url)).hostname not in ("asasmakeen.com","www.asasmakeen.com"):raise ValueError("NOT_FIRSTPARTY_REDIRECT")
 return r
try:
 robot=fetch("https://"+HOST+"/robots.txt")
 if int(robot.status)!=200:raise RuntimeError("ROBOTS_UNAVAILABLE_"+str(robot.status))
 rp=RobotFileParser();rp.parse(robot.body.decode("utf-8","replace").splitlines())
 seen=set()
 for project,url in URLS.items():
  if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW_"+project)
  time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=fetch(url)
  if int(r.status)!=200:raise RuntimeError("SOURCE_HTTP_"+project+"_"+str(r.status))
  root=LX.fromstring(r.body.decode('utf-8','replace'))
  heading=txt(root.xpath("//h1[1]")[0]) if root.xpath("//h1[1]") else ""
  expected="مكين "+project
  if heading!=expected:raise RuntimeError("UNEXPECTED_PUBLISHER_PROJECT_"+heading)
  rows=root.xpath('//tr[contains(concat(" ",normalize-space(@class)," ")," unit-row ")]')
  per={"project":project,"publisher_title":heading,"url":str(r.url),"source_rows":len(rows),"status_counts":{},"code_pattern_failures":[]}
  for row in rows:
   tds=row.xpath("./td")
   if not tds:continue
   code=txt(tds[0])
   if not re.fullmatch(r"[A-Z]\d{1,4}[A-Z]-"+project,code,re.I):
    per["code_pattern_failures"].append(code);continue
   key=project+"|"+code.upper()
   if key in seen:raise RuntimeError("DUPLICATE_PHYSICAL_SOURCE_KEY_"+key)
   seen.add(key)
   full=txt(row)
   badge=row.xpath('.//span[contains(@class,"status-badge")]')
   badge_text=txt(badge[0]) if badge else ""
   flag=row.get("data-flag") or ""
   is_inactive=len(tds)<6
   if is_inactive and badge_text:
    status={"مباع":"SOLD","محجوز":"RESERVED","مؤجر":"RENTED"}.get(badge_text,"UNCLASSIFIED_"+badge_text)
   elif "rent" in flag.lower() or ("إيجار" in txt(tds[-1])):
    status="RENT_ADVERTISED"
   elif "sale" in flag.lower():
    status="SALE_ADVERTISED"
   else:
    status="ACTIVE_STATUS_UNVERIFIED"
   floor=txt(tds[1]).replace("المخطط","").replace("360 / جولة","").strip() if len(tds)>=6 else ""
   area_text=txt(tds[2]) if len(tds)>=6 else ""
   area=float(area_text.replace(",","")) if re.fullmatch(r"\d+(?:\.\d+)?",area_text.replace(",","")) else None
   room_text=txt(tds[3]) if len(tds)>=6 else ""
   beds=int(room_text) if room_text.isdigit() else None
   features=txt(tds[4])[:400] if len(tds)>=6 else ""
   price_text=txt(tds[5]) if len(tds)>=6 else ""
   price=None
   match=re.search(r"\b\d[\d,]*(?:\.\d+)?\b",price_text)
   if match:
    v=match.group().replace(",","")
    if v.isdigit():price=int(v)
   if is_inactive:price=None
   card={"publisher_project_no":project,"original_unit_code":code,
      "publisher_status":status,"status_original":badge_text or flag,
      "floor_original":floor or None,"area_sqm_visible":area,"rooms_visible":beds,
      "public_visible_price_sar":price,"public_price_text":price_text[:150],
      "price_context":"RENT_PERIOD_UNKNOWN" if status=="RENT_ADVERTISED" else "SALE_ASK" if status=="SALE_ADVERTISED" else "UNVERIFIED_OR_NO_VISIBLE_AMOUNT",
      "features":features,"html_data_room":row.get("data-room"),"html_data_distance":row.get("data-distance"),"html_data_price":row.get("data-price"),
      "source_url":str(r.url)}
   state["cards"].append(card)
   per["status_counts"][status]=per["status_counts"].get(status,0)+1
  state["pages"].append(per);save()
  print("MAKEEN_FIRSTPARTY_PROJECT "+json.dumps(per,ensure_ascii=False,separators=(",",":")))
 if any(x["code_pattern_failures"] for x in state["pages"]):raise RuntimeError("SOURCE_UNIT_IDENTITY_PATTERN_NOT_UNIFORM")
 if any(x["source_rows"]!=sum(x["status_counts"].values()) for x in state["pages"]):raise RuntimeError("PARTIAL_SOURCE_PARSING")
 if len(state["cards"])<100:raise RuntimeError("LOW_EXTRACTED_COUNT")
 state["status"]="COMPLETE_FIRSTPARTY_SOURCE_UNITS"
except Exception as ex:
 state["status"]="STOPPED_429" if "HTTP_429_GLOBAL" in str(ex) else "STOPPED_ERROR"
 state["errors"].append({"error":type(ex).__name__+": "+str(ex)[:240]})
finally:
 save()
 print("MAKEEN_FIRSTPARTY_SUMMARY "+json.dumps({"status":state["status"],"projects":len(state["pages"]),
   "original_itemized_cards":len(state["cards"]),"distinct_original_keys":len({r["publisher_project_no"]+"|"+r["original_unit_code"] for r in state["cards"]}),
   "errors":state["errors"]},ensure_ascii=False,separators=(",",":")))
 for i in range(0,len(state["cards"]),12):print("MAKEEN_SOURCE_CARDS_JSON "+json.dumps(state["cards"][i:i+12],ensure_ascii=False,separators=(",",":")))
