#!/usr/bin/env python3
"""SAE Source Intelligence V2: AlsOliman actual original unit inventory.
Read-only, robots-gated: 132 Aress Riyadh + 133 Sakenah Makkah.
Scrapling 0.5 Fetcher + standard Playwright to compare static and JS, discover
filter/pagination/XHR data without guessing URLs or manufacturing missing units.
"""
from __future__ import annotations
import json,os,re,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit,urljoin,urlunsplit
from collections import Counter
from scrapling.fetchers import Fetcher
from lxml import html as LX
from playwright.sync_api import sync_playwright

HOST="www.alsoliman.com.sa"
ROOT="https://"+HOST
PROJECTS=[
("Sakenah133",ROOT+"/ar/selling/project/Sakenah-compound-makkah"),
("Aress132",ROOT+"/ar/selling/project/AressCompound132")
]
UA="SAE-SiteIntelligence-AlSoliman-ReadOnly/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"sae_alsoliman_two_projects_deep_source.json"
state={"schema":"SAE_SITE_INTEL_ALSOLIMAN_132_133_PUBLISHED_UNIT_EXACT_V2",
       "at":datetime.now(timezone.utc).isoformat(),"status":"START",
       "projects":[],"errors":[],"production_writes":0,"source_only":True}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def text(el):return " ".join(" ".join(el.itertext()).split()) if el is not None else ""
def extract(html_text):
    dom=LX.fromstring(html_text)
    cards=dom.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," apartment-col ")]')
    result=[];invalid=[];seen=set()
    for el in cards:
        child=el.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," apartment-item ")]')
        if not child:invalid.append({"reason":"NO_APARTMENT_ITEM"});continue
        item=child[0]
        blocks=item.xpath('./div[contains(concat(" ",normalize-space(@class)," ")," apartment-item-row ")]')
        chunks=[[text(s) for s in row.xpath('./span')] for row in blocks[:3]]
        if len(chunks)<2:invalid.append({"reason":"NO_ROWS","sample":text(item)[:140]});continue
        labels=dict(zip(chunks[0],chunks[1]))
        code=labels.get("الوحدة","")
        building=labels.get("العمارة","")
        area=labels.get("المساحة","")
        if not re.fullmatch(r"[A-Z]",building,re.I) or not re.fullmatch(r"\d{2,4}",code) or not re.fullmatch(r"\d+(?:\.\d+)?",area):
            invalid.append({"reason":"NO_VERIFIED_PHYSICAL_ID","fields":labels});continue
        composite=building+"-"+code
        if composite in seen:invalid.append({"reason":"DUPLICATE_PUBLISHER_CODE","code":composite});continue
        seen.add(composite)
        status_raw=re.search(r"\bstatus-([012])\b",el.get("class") or "")
        status={"0":"available","1":"reserved","2":"sold"}.get(status_raw.group(1) if status_raw else "",None)
        pub_id=item.get("data-id")
        ask_nodes=item.xpath('.//*[contains(@class,"price")]')
        original_price=" ".join(text(x) for x in ask_nodes)[:100]
        ask_match=re.search(r"(?<!\d)([1-9]\d{5,7})(?!\d)", original_price.replace(",","").replace(" ",""))
        result.append({"code":composite,"unit_number":code,"building":building,
            "area_sqm":float(area),"floor_original":labels.get("الدور"),
            "rooms_original":labels.get("الغرف"),"model_original":labels.get("النموذج"),
            "publisher_original_id":pub_id,"publisher_status":status,
            "listed_price_sar":int(ask_match.group(1)) if ask_match else None,
            "price_raw":original_price,"context":text(item)[:400]})
    return {"html_container_count":len(cards),"verified_cards":result,
            "invalid":invalid[:40],"distinct_verified":len(result),
            "statuses":dict(Counter(c["publisher_status"] for c in result))}

def safe_url(url):
    p=urlsplit(str(url))
    return urlunsplit((p.scheme,p.netloc,p.path,"",""))[:300]

def get(url):
    r=Fetcher.get(url,retries=0,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
    if int(r.status)==429:raise RuntimeError("GLOBAL_HTTP429_STOP")
    if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status)+" "+url)
    if urlsplit(str(r.url)).hostname!=HOST:raise RuntimeError("OFF_HOST_REDIRECT")
    return r.body.decode("utf8","replace")
try:
    rp=RobotFileParser()
    rb=get(ROOT+"/robots.txt");rp.parse(rb.splitlines())
    delay=max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
    for key,url in PROJECTS:
        rec={"key":key,"url":url,"status":"START","errors":[]}
        state["projects"].append(rec)
        if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DENY_"+key)
        time.sleep(delay)
        source=get(url)
        rec["static"]=extract(source)
        rec["static"]["scripts_count"]=len(re.findall(r'<script\b',source,re.I))
        rec["static"]["html_bytes"]=len(source.encode("utf8"))
        rec["static"]["pager_keywords"]={k:len(re.findall(k,source,re.I)) for k in
             ("pagination","pageCount","loadMore","unit-list","filter","status-2","status-1")}
        save()
        time.sleep(delay)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                page=browser.new_page()
                requests=[]
                page.on("response",lambda r: requests.append(r))
                nav=page.goto(url,wait_until="domcontentloaded",timeout=40000)
                if nav and nav.status==429:raise RuntimeError("GLOBAL_HTTP429_STOP")
                page.wait_for_timeout(1900)
                rec["browser"]=extract(page.content())
                rec["browser"]["buttons"]=[]
                for b in page.locator("button").all()[:100]:
                    rec["browser"]["buttons"].append({"text":b.inner_text()[:90],
                         "id":b.get_attribute("id"),"class":(b.get_attribute("class") or "")[:110]})
                rec["browser"]["selects"]=[]
                for s in page.locator("select").all()[:30]:
                    rec["browser"]["selects"].append({"id":s.get_attribute("id"),"name":s.get_attribute("name"),
                         "options":[{"v":x.get_attribute("value"),"t":x.inner_text()[:80]}
                             for x in s.locator("option").all()[:70]]})
                rec["browser"]["paginators"]=[x.inner_text()[:250] for x in page.locator(
                   "[class*='pagination'],[class*='paging'],[id*='pagination'],[id*='paging']").all()[:25]]
                rec["browser"]["unit_tab_text"]=[x.inner_text()[:140] for x in page.locator(
                   ".nav-tabs a,.nav-tabs button,[role='tab'],[data-filter]").all()[:80]]
                rec["browser"]["xhr"]=[]
                for response in requests:
                    if response.status==429:raise RuntimeError("GLOBAL_HTTP429_STOP")
                    if response.request.resource_type not in ("xhr","fetch"):continue
                    if urlsplit(response.url).hostname!=HOST:continue
                    if len(rec["browser"]["xhr"])>=50:break
                    e={"url":safe_url(response.url),"http":response.status,
                       "method":response.request.method}
                    if response.status==200:
                        try:
                            val=json.loads(response.body())
                            if isinstance(val,list):
                                e["json_array_count"]=len(val)
                                e["first_item_keys"]=list(val[0])[:30] if val and isinstance(val[0],dict) else []
                            elif isinstance(val,dict):
                                e["json_keys"]=list(val)[:40]
                                e["json_array_sizes"]={k:len(v) for k,v in val.items() if isinstance(v,list)}
                        except (ValueError,UnicodeDecodeError):pass
                    rec["browser"]["xhr"].append(e)
                rec["status"]="COMPLETE"
            finally:browser.close()
        print("ALSOLIMAN_SITE_INTEL "+json.dumps({"key":key,
            "static":rec["static"]["distinct_verified"],
            "browser":rec.get("browser",{}).get("distinct_verified"),
            "buttons":len(rec.get("browser",{}).get("buttons",[])),
            "selects":len(rec.get("browser",{}).get("selects",[])),
            "xhr":len(rec.get("browser",{}).get("xhr",[]))},ensure_ascii=False),flush=True)
        save()
    state["status"]="COMPLETE_2_FIRSTPARTY_PROJECTS"
except Exception as e:
    state["status"]="GLOBAL_STOP_429" if "GLOBAL_HTTP429_STOP" in str(e) else "STOP_SOURCE_ERROR"
    state["errors"].append(type(e).__name__+": "+str(e)[:350])
finally:
    save()
    print("FINAL "+json.dumps({"status":state["status"],"n":len(state["projects"]),"errors":state["errors"]},ensure_ascii=False),flush=True)
if state["status"]!="COMPLETE_2_FIRSTPARTY_PROJECTS":raise SystemExit(1)
