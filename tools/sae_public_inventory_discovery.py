#!/usr/bin/env python3
"""SAE public project inventory probe, source-only, no Sheets writes.

Observe publisher first-party pages, linked developer map, and public XHR.
Never infer physical units from project totals or generic floorplan models.
"""
import asyncio
import hashlib
import json
import os
import urllib.parse
import urllib.robotparser
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEEDS = [
 {"id":"PRJ-001093","name":"Saraya Al Narjis","url":"https://digitalpartnersglobal.com/darwa/?lang=ar&view=riyadh"},
 {"id":"PRJ-000046","name":"Nesaj Lazurd","url":"https://verse.retal.com.sa/?lang=en&state=saudi_arabia&theme=light"},
 {"id":"PRJ-001484","name":"Green Oasis","url":"https://alargan.com.sa/green-oasis/"},
 {"id":"PRJ-001487","name":"Suhool","url":"https://alargan.com.sa/suhool/"},
 {"id":"PRJ-000051","name":"Ewan Khuzam","url":"https://retal.com.sa/en/properties/ewan-khuzam/"}
]
CODE_FIELDS = ["unitCode","unit_code","landNumber","villaNumber","unitNumber","plotNumber"]
UA = "SAE-DB-SourceStudy/1.0"
def robots_allow(url):
    p = urllib.parse.urlsplit(url)
    path = p.scheme + "://" + p.netloc + "/robots.txt"
    try:
        req=urllib.request.Request(path,headers={"User-Agent":UA})
        with urllib.request.urlopen(req,timeout=14) as r:
            if r.status != 200:return False,"ROBOTS_HTTP_"+str(r.status)
            contents=r.read(300000).decode("utf-8","replace")
        rp=urllib.robotparser.RobotFileParser()
        rp.parse(contents.splitlines())
        return rp.can_fetch(UA,url),"ROBOTS_READ"
    except Exception as e:return False,"ROBOTS_UNVERIFIED_"+type(e).__name__

def unit_arrays(obj):
    queue=[obj]; found=[]
    while queue:
        item=queue.pop()
        if isinstance(item,dict):
            queue.extend(item.values())
        elif isinstance(item,list):
            if len(item)>=20 and all(isinstance(q,dict) for q in item[:20]):
                for key in CODE_FIELDS:
                    vals=[str(r.get(key,"")).strip() for r in item]
                    if all(v and v.lower() not in ("null","none","0") for v in vals) and len(set(vals))==len(vals):
                        found.append({"count":len(item),"field":key,"sample":vals[:8],
                                      "public_unit_fields_only":[
                                        {k:v for k,v in row.items()
                                         if k in ("unitCode","unit_code","unitNumber","landNumber",
                                                  "villaNumber","plotNumber","building","buildingNo",
                                                  "block","floor","area","area_sqm","price",
                                                  "price_sar","status","available","real_available",
                                                  "bedrooms","bathrooms","model","type")
                                         and isinstance(v,(str,int,float,bool,type(None)))}
                                        for row in item]})
            queue.extend(item[:15])
    return sorted(found,key=lambda x:x["count"],reverse=True)[:3]

async def probe(seed,browser):
    report=dict(seed,started_utc=datetime.now(timezone.utc).isoformat(),network=[],links=[])
    allow,why=await asyncio.to_thread(robots_allow,seed["url"])
    report.update(robots=why,robots_allowed=allow)
    if not allow:return report
    page=await browser.new_page()
    tasks=[]
    stop=False
    async def resp(r):
        nonlocal stop
        if r.status in (403,429):
            # Only stop when main page or its same publisher API is blocked.
            host=urllib.parse.urlsplit(seed["url"]).hostname or ""
            rh=urllib.parse.urlsplit(r.url).hostname or ""
            if rh==host or rh.endswith("."+host):stop=True
        ctype=r.headers.get("content-type","")
        if r.status!=200 or (r.request.resource_type not in ("xhr","fetch") and "json" not in ctype):return
        if len(report["network"])>=120:return
        try:
            data=await r.body()
            if len(data)>10000000:return
            info={"url":r.url,"size":len(data),"sha256":hashlib.sha256(data).hexdigest(),
                  "type":ctype,"sample":data[:400].decode("utf-8","replace")}
            try:
                blob=json.loads(data)
                info["arrays"]=unit_arrays(blob)
                if info["arrays"] and len(report.setdefault("candidate_original_records",[]))<8:
                    # Keep original fields only for discovered real unique coded inventories.
                    report["candidate_original_records"].append({"source":r.url,"unit_arrays":info["arrays"]})
            except Exception:pass
            report["network"].append(info)
        except Exception as e:
            report.setdefault("errors",[]).append("response:"+type(e).__name__)
    page.on("response",lambda r:tasks.append(asyncio.create_task(resp(r))))
    try:
        res=await page.goto(seed["url"],wait_until="domcontentloaded",timeout=45000)
        report["main_status"]=res.status if res else None
        if report["main_status"] not in (403,429) and not stop:
            await page.wait_for_timeout(12000)
            report["title"]=await page.title()
            report["links"]=await page.locator("a[href]").evaluate_all(
                "(a)=>a.map(x=>({text:(x.innerText||'').trim().slice(0,60),href:x.href}))"
                ".filter(x=>/interactive|map|الوحدات|المخطط|الخريطة|master/i.test(x.text+' '+x.href))"
                ".slice(0,40)")
    except Exception as e:report.setdefault("errors",[]).append("page:"+str(e)[:200])
    if tasks:await asyncio.gather(*tasks,return_exceptions=True)
    await page.close()
    report["stop_access"]=stop
    return report

async def main():
    from playwright.async_api import async_playwright
    outputs={"schema":"SAE_SOURCE_ONLY_PUBLIC_INTERACTIVE_DISCOVERY_V1","generated_utc":datetime.now(timezone.utc).isoformat(),
             "sheets_mutations":0,"results":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for seed in SEEDS:
            try:result=await probe(seed,browser)
            except Exception as e:result=dict(seed,error=str(e)[:240])
            outputs["results"].append(result)
            Path("sae-public-source-discovery.json").write_text(json.dumps(outputs,ensure_ascii=False,indent=2))
            print(seed["id"],result.get("main_status"),result.get("robots"),len(result.get("network",[])),
                  len(result.get("candidate_original_records",[])),flush=True)
            if result.get("stop_access"):
                print("SOURCE_ACCESS_BLOCKED; stop this publisher",flush=True)
        await browser.close()

if __name__=="__main__":
    assert unit_arrays({"marketing_units":1064,"models":[{"count":556}]})==[]
    assert unit_arrays({"inventory":[{"unitCode":str(i+1)} for i in range(30)]})[0]["count"]==30
    assert unit_arrays({"inventory":[{"unitCode":"A"} for _ in range(30)]})==[]
    asyncio.run(main())
