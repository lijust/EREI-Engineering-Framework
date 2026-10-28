#!/usr/bin/env python3
"""SAE units-only first-party Tamayaz 8 table, source-only; exact displayed rows."""
import json,os,re,sys,time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html
HOST="tamayaz.com.sa"
PAGE="https://tamayaz.com.sa/project/%D8%A7%D8%B3%D9%85-%D8%A7%D9%84%D9%85%D8%B4%D8%B1%D9%88%D8%B9-02/"
UA="SAE-DB-public-firstparty-numbered-residential-unit-research/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"tamayaz8_exact_original_source_units.json"
data={"schema":"SAE_TAMAYAZ8_FIRSTPARTY_42_EXACT_PUBLISHER_CODES_V1","source_url":PAGE,"cards":[],"table_shapes":[],"status":"STARTED","errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf8")
def get(url):
 p=urlparse(url)
 if p.hostname!=HOST or p.scheme!="https":raise RuntimeError("OFF_PUBLISHER")
 r=Fetcher.get(url,retries=0,timeout=90,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP429_STOP")
 if int(r.status)!=200:raise RuntimeError("SOURCE_HTTP_"+str(r.status))
 if urlparse(str(r.url)).hostname!=HOST:raise RuntimeError("OFF_PUBLISHER_REDIRECT")
 return r.body
try:
 rb=get("https://tamayaz.com.sa/robots.txt")
 rp=RobotFileParser();rp.parse(rb.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,PAGE):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 body=get(PAGE)
 root=html.fromstring(body)
 seen=set()
 for ti,table in enumerate(root.xpath("//table")):
  rows=table.xpath(".//tr")
  count=0
  for tr in rows:
   values=[" ".join(" ".join(td.itertext()).split()) for td in tr.xpath("./td|./th")]
   if len(values)<4:continue
   building,code,area,status=values[:4]
   if not re.fullmatch(r"[A-F]",building) or not re.fullmatch(r"[A-F]0[1-7]",code) or code[0]!=building:continue
   a=area.replace(",","").replace("م²","").strip()
   if not re.fullmatch(r"\\d+(?:\\.\\d+)?",a):
    data["errors"].append({"reason":"INVALID_AREA","row":values});continue
   if code in seen:raise RuntimeError("DUPLICATE_EXACT_CODE_"+code)
   seen.add(code);count+=1
   data["cards"].append({"publisher_building":building,"publisher_original_unit_code":code,"source_area_sqm":float(a),
                         "publisher_original_status":status,"source_page_url":PAGE,"table_index":ti,"original_table_cells":values})
  data["table_shapes"].append({"table_index":ti,"html_rows":len(rows),"accepted_exact_units":count})
 if len(data["cards"])!=42 or len(seen)!=42:raise RuntimeError("EXPECTED_EXACT_42_BUT_GOT_"+str(len(data["cards"])))
 if data["errors"]:raise RuntimeError("VALIDATION_ERRORS")
 data["status"]="COMPLETE_42_SOURCE_EXACT_PUBLISHER_ROWS"
except Exception as e:
 data["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 data["errors"].append(str(e)[:450])
finally:
 save()
 print("TAMAYAZ8_EXACT_SUMMARY "+json.dumps({"status":data["status"],"cards":len(data["cards"]),"table_shapes":data["table_shapes"],"errors":data["errors"],"master_writes":0},ensure_ascii=False),flush=True)
 for i in range(0,len(data["cards"]),12):
  print("TAMAYAZ8_SOURCE_CARDS_JSON "+json.dumps(data["cards"][i:i+12],ensure_ascii=False,separators=(",",":")),flush=True)
if data["status"]!="COMPLETE_42_SOURCE_EXACT_PUBLISHER_ROWS":sys.exit(2)
