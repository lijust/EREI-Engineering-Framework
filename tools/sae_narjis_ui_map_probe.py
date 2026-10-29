#!/usr/bin/env python3
"""Source-only examination of developer-linked Narjis interactive map after public UI tutorial.

No login, no protected endpoint access, no Sheets writes. One navigation,
then clicks only the map's public explanatory and browsing UI controls.
"""
import asyncio,hashlib,json,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright

URL="https://digitalpartnersglobal.com/darwa/?lang=ar&view=riyadh"
UA="SAE-DB-public-source-study/1.0"
REPORT={"project":"Saraya Al Narjis","canonical_candidate":"PRJ-001093",
        "source_url":URL,"run_utc":datetime.now(timezone.utc).isoformat(),
        "production_writes":0,"responses":[],"ui_snapshots":[],"errors":[]}

def allow():
    p=urllib.robotparser.RobotFileParser()
    with urllib.request.urlopen(urllib.request.Request(
            "https://digitalpartnersglobal.com/robots.txt",headers={"User-Agent":UA}),timeout=15) as f:
        if f.status!=200:return False
        p.parse(f.read(200000).decode("utf-8","replace").splitlines())
    return p.can_fetch(UA,URL)

async def snapshot(page,stage):
    data=await page.evaluate("""() => ({
      title:document.title,body_text:(document.body?.innerText||'').slice(0,3500),
      svgs:document.querySelectorAll('svg').length,
      svg_shapes:document.querySelectorAll('svg polygon,svg path,svg rect').length,
      canvas:document.querySelectorAll('canvas').length,
      data_nodes:[...document.querySelectorAll('[data-id],[data-unit],[data-number],[data-plot],[title]')].slice(0,85).map(el=>({tag:el.tagName,text:(el.textContent||'').trim().slice(0,80),data:el.dataset,
      title:el.getAttribute('title')})),
      scripts:[...document.querySelectorAll('script[src]')].map(x=>x.src).slice(0,25),
      links:[...document.querySelectorAll('a[href]')].slice(0,30).map(x=>({text:(x.textContent||'').trim().slice(0,80),href:x.href}))
    })""")
    REPORT["ui_snapshots"].append({"stage":stage,**data})
    await page.screenshot(path="sae-narjis-map-"+stage+".png")
    Path("sae-narjis-original-public-ui.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))

async def main():
    try:
        permitted=await asyncio.to_thread(allow)
    except Exception as e:
        permitted=False
        REPORT["errors"].append("robots_unverified:"+type(e).__name__)
    REPORT["robots_permitted"]=permitted
    if not permitted:
        Path("sae-narjis-original-public-ui.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
        return
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(user_agent=UA,viewport={"width":1440,"height":960})
        tasks=[]
        blocked=False
        async def capture(r):
            nonlocal blocked
            if r.status in (403,429) and "digitalpartnersglobal.com" in r.url:
                blocked=True
                REPORT["errors"].append("access_control:"+str(r.status)+":"+r.url[:160])
                return
            if r.status!=200:return
            kind=r.request.resource_type
            if kind not in ("xhr","fetch","script","document"):return
            try:
                b=await r.body()
                info={"url":r.url,"kind":kind,"size":len(b),"sha256":hashlib.sha256(b).hexdigest()}
                if kind in ("xhr","fetch"):
                    if len(b)<6000000:
                        try:
                            js=json.loads(b)
                            info["json_type"]=type(js).__name__
                            info["json_keys"]=list(js)[:35] if isinstance(js,dict) else []
                            # Preserve sampled original public per-unit keys without exporting PII.
                            if isinstance(js,dict):
                                info["unit_related_keys"]=[k for k in js if any(s in k.lower() for s in ("unit","villa","block","plot","inventory"))]
                        except Exception:info["sample"]=b[:120].decode("utf-8","replace")
                if kind=="script" and "digitalpartnersglobal.com" in r.url:
                    s=b.decode("utf-8","replace")
                    pats=("unitCode","unitNumber","villaNumber","plotNumber","inventory","api/","units","landNumber")
                    info["keyword_occurrences"]={x:s.lower().count(x.lower()) for x in pats}
                    info["snippet_contexts"]=[]
                    for needle in ("inventory","unitCode","villaNumber","landNumber","api/"):
                        ix=s.lower().find(needle.lower())
                        if ix>=0:info["snippet_contexts"].append(s[max(0,ix-160):ix+240])
                REPORT["responses"].append(info)
            except Exception as e:
                REPORT["errors"].append("response:"+type(e).__name__)
        page.on("response",lambda r:tasks.append(asyncio.create_task(capture(r))))
        try:
            r=await page.goto(URL,wait_until="domcontentloaded",timeout=40000)
            REPORT["http_status"]=r.status if r else None
            if REPORT["http_status"] not in (403,429) and not blocked:
                await page.wait_for_timeout(6500)
                await snapshot(page,"before")
                for label,stage in [("تخطى التعليمات","after_skip"),("عرض الكل","show_all"),("عرض النماذج","models")]:
                    if blocked:break
                    item=page.get_by_text(label,exact=False)
                    if await item.count()==0:
                        REPORT["errors"].append("UI_LABEL_NOT_FOUND:"+label)
                        continue
                    try:
                        await item.first.click(timeout=5500)
                        await page.wait_for_timeout(5500)
                        await snapshot(page,stage)
                    except Exception as e:REPORT["errors"].append(stage+":"+type(e).__name__)
        except Exception as e:REPORT["errors"].append("page:"+str(e)[:220])
        if tasks:await asyncio.gather(*tasks,return_exceptions=True)
        await browser.close()
    Path("sae-narjis-original-public-ui.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
    print(json.dumps({"snapshots":[x["stage"] for x in REPORT["ui_snapshots"]],
      "responses":len(REPORT["responses"]),"errors":REPORT["errors"][:15]},ensure_ascii=False))

if __name__=="__main__":asyncio.run(main())
