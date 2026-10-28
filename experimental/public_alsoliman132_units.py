#!/usr/bin/env python3
"""First-party licensed public pages only: itemized AressCompound132 unit cards."""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from lxml import html as LX
from scrapling.fetchers import Fetcher
HOST="www.alsoliman.com.sa"
URL="https://www.alsoliman.com.sa/ar/selling/project/AressCompound132"
UA="SAE-DB-source-only-unit-cards/1.0"
OUT=Path(os.environ["RUNNER_TEMP"])/"alsoliman132_firstparty_itemized_cards.json"
state={"schema":"FIRST_PARTY_ALSOLIMAN_ARESS132_PUBLISHED_UNIT_SNAPSHOT_V1","source_url":URL,
       "project_name":None,"status":"STARTED","declared_units":None,"cards":[],
       "errors":[],"private_canonical_data_used":False,"master_sheet_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def text_of(x):return " ".join(" ".join(x.itertext()).split()) if x is not None else ""
def source_get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or p.path not in ("/robots.txt",urlsplit(URL).path):
  raise ValueError("NOT_APPROVED_PUBLISHER_URL")
 r=Fetcher.get(url,retries=1,timeout=40,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("429_HALT_NO_RETRY")
 if urlsplit(str(r.url)).hostname!=HOST:raise ValueError("OFF_PUBLISHER_REDIRECT")
 return r
try:
 rr=source_get("https://"+HOST+"/robots.txt")
 if int(rr.status)!=200:raise RuntimeError("ROBOTS_UNAVAILABLE_"+str(rr.status))
 robots=RobotFileParser();robots.parse(rr.body.decode("utf-8","replace").splitlines())
 if not robots.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3.0,float(robots.crawl_delay(UA) or robots.crawl_delay("*") or 0)))
 res=source_get(URL)
 if int(res.status)!=200:raise RuntimeError("SOURCE_HTTP_"+str(res.status))
 root=LX.fromstring(res.body)
 state["project_name"]=" ".join(root.xpath("//h1[1]//text()")).strip()
 cards=root.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," apartment-col ")]')
 state["html_card_containers"]=len(cards)
 all_codes=set()
 for container in cards:
  classes=" "+str(container.get("class") or "")+" "
  match=re.search(r"\bstatus-([012])\b",classes)
  status={"0":"PUBLISHER_FOR_SALE","1":"PUBLISHER_RESERVED","2":"PUBLISHER_SOLD"}.get(match.group(1) if match else "",None)
  item=container.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," apartment-item ")]')
  if len(item)!=1:
   state["errors"].append({"error":"CARD_STRUCTURE","count":len(item)});continue
  rootitem=item[0]
  pub_unit_id=rootitem.get("data-id")
  rows=rootitem.xpath('./div[contains(concat(" ",normalize-space(@class)," ")," apartment-item-row ")]')
  table=[]
  for row in rows[:3]:
   spans=row.xpath('./span')
   table.append([text_of(s) for s in spans])
  sample={"id":pub_unit_id,"row_structure":table,"status":status,"text":text_of(rootitem)[:300]}
  if len(table)<2 or len(table[1])<5:
   state["errors"].append({"error":"MISSING_UNIT_CELLS","sample":sample});continue
  header=table[0]
  values=table[1]
  fields={k:v for k,v in zip(header,values)}
  number=fields.get("الوحدة","")
  floor=fields.get("الدور","")
  building=fields.get("العمارة","")
  area_raw=fields.get("المساحة","")
  beds_raw=fields.get("الغرف","")
  model=fields.get("النموذج","")
  if not re.fullmatch(r"[A-Z]",building,re.I) or not re.fullmatch(r"\d{2,4}",number) or not re.fullmatch(r"\d+(?:\.\d+)?",area_raw):
   state["errors"].append({"error":"BAD_CARD_IDENTITY","sample":sample});continue
  code=building.upper()+"-"+number
  if code in all_codes:raise ValueError("DUPLICATE_ORIGINAL_BUILDING_AND_DOOR_"+code)
  all_codes.add(code)
  status_visible=(rootitem.xpath('.//*[contains(@class,"-bg")]/text()') or [])
  status_text=" ".join(x.strip() for x in status_visible if x.strip())
  detail_nodes=rootitem.xpath('.//div[contains(@class,"apartment-item-desc")]')
  detail=" ".join(text_of(x) for x in detail_nodes)[:1000]
  price_nodes=rootitem.xpath('.//*[contains(@class,"price")]')
  price_text=" ".join(text_of(x) for x in price_nodes)[:160]
  price=None
  n=re.search(r"(?<!\d)([1-9]\d{5,7})(?!\d)",price_text.replace(",","").replace(" ",""))
  if n:price=int(n.group(1))
  state["cards"].append({"publisher_unit_id":pub_unit_id,"source_unit_code":code,
    "unit_number":number,"building_no":building.upper(),"floor_original":floor,"publisher_model":model,
    "area_sqm":float(area_raw),"bedrooms":int(beds_raw) if beds_raw.isdigit() else None,
    "publisher_status":status,"publisher_status_visible":status_text,
    "source_bathroom_detail":detail,"source_asking_price_sar_ex_vat":price,
    "source_price_text":price_text})
 if len(state["cards"])<10:raise RuntimeError("INSUFFICIENT_EXTRACTED_CARDS")
 if state["errors"]:raise RuntimeError("PARSER_HAS_"+str(len(state["errors"]))+"_CARD_ERRORS")
 state["status"]="COMPLETE_FIRSTPARTY_ITEMIZED_CARDS"
except Exception as ex:
 state["status"]="STOPPED_429" if "429_HALT" in str(ex) else "STOPPED_ERROR"
 state["errors"].append({"error":type(ex).__name__+": "+str(ex)[:230]})
finally:
 save()
 print("FIRSTPARTY_SOLIMAN_SUMMARY "+json.dumps({"status":state["status"],"project":state["project_name"],
   "html_cards":state.get("html_card_containers"),"valid_cards":len(state["cards"]),
   "status_counts":{k:sum(x["publisher_status"]==k for x in state["cards"]) for k in ["PUBLISHER_FOR_SALE","PUBLISHER_RESERVED","PUBLISHER_SOLD",None]},
   "priced":sum(x["source_asking_price_sar_ex_vat"] is not None for x in state["cards"]),
   "errors":state["errors"][:3]},ensure_ascii=False,separators=(",",":")))
 for i in range(0,len(state["cards"]),12):print("SOURCE_UNIT_CARDS_JSON "+json.dumps(state["cards"][i:i+12],ensure_ascii=False,separators=(",",":")))
