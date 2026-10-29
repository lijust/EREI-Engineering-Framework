#!/usr/bin/env python3
"""Deep per-unit public Menaco listing pagination (existing SAE projects only).

No synthesized A1..A51 sequences, no database writes, no login and no bypass.
Capture exactly displayed original card codes from the browser after actual UI
load-more interaction, not advertised project totals.
"""
from __future__ import annotations
import asyncio, hashlib, json, re, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

SOURCE = [
    {"project_id":"PRJ-001802","url":"https://menaco.sa/index.php/listings/276031","name":"Mena 51"},
    {"project_id":"PRJ-001803","url":"https://menaco.sa/listings/865393","name":"Mena 52"}
]
UA="SAE-DB-Menaco-original-public-unit-inventory/1.0"
OUT=Path("sae-menaco-51-52-original-pagination.json")
CODES_51=re.compile(r"^A\d{1,3}$")
CODES_52=re.compile(r"^(?:A\d{1,3}|\d{1,2}/\d{1,2})$")
def check_robots(url):
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname not in ("menaco.sa","www.menaco.sa"):
        raise ValueError("SOURCE_NOT_MENACO")
    with urllib.request.urlopen(urllib.request.Request("https://menaco.sa/robots.txt",headers={"User-Agent":UA}),timeout=15) as r:
        if r.status!=200:return False,"ROBOTS_HTTP_"+str(r.status)
        data=r.read(150001)
    if len(data)>150000:return False,"ROBOTS_TOO_LARGE"
    rp=RobotFileParser();rp.parse(data.decode("utf8","replace").splitlines())
    return rp.can_fetch(UA,url),"ROBOTS_CHECKED"

def normalized_original_cards(raw_text, project_id):
    """Use original visible unit-list text only; never marketing totals."""
    if "الوحدات المتاحة" not in raw_text:
        return []
    segment = raw_text.split("الوحدات المتاحة", 1)[1].split("خدمة العملاء المجانية", 1)[0]
    lines = [x.strip() for x in segment.splitlines() if x.strip()]
    codepat = CODES_51 if project_id == "PRJ-001802" else CODES_52
    positions = [i for i, line in enumerate(lines) if codepat.fullmatch(line)]
    result = []
    for index, start in enumerate(positions):
        stop = positions[index+1] if index+1 < len(positions) else len(lines)
        block = lines[start+1:stop]
        content = "\n".join(block)
        area = re.search(r"(?m)^(\d+(?:\.\d+)?)\s*متر مربع$", content)
        bedrooms = re.search(r"(?m)^(\d+)\s*غرفة نوم$", content)
        bathrooms = re.search(r"(?m)^(\d+)\s*حمام$", content)
        statuses = [line for line in block if line in ("للبيع", "محجوز", "مباع")]
        price = re.fullmatch(r"\d{1,3}(?:,\d{3})+", block[0]) if block else None
        row = {
            "project_id": project_id, "original_unit_code": lines[start],
            "area_sqm": float(area.group(1)) if area else None,
            "bedrooms": int(bedrooms.group(1)) if bedrooms else None,
            "bathrooms": int(bathrooms.group(1)) if bathrooms else None,
            "published_price_sar": int(price.group().replace(",", "")) if price else None,
            "source_status_ar": statuses[0] if len(statuses)==1 else None,
            "original_card_text": "\n".join([lines[start]]+block[:12])[:500],
            "source_snapshot_not_live": True
        }
        row["qualifies_physical"] = bool(row["area_sqm"] and row["bedrooms"] and
                                         row["bathrooms"] and row["source_status_ar"])
        result.append(row)
    return result

def save(doc):
    t=OUT.with_suffix(".tmp")
    t.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    t.replace(OUT)
EVAL=r"""() => {
 const section=[...document.querySelectorAll('h2,h3,h4,h5')].find(x=>/الوحدات المتاحة|Available Units/i.test(x.innerText||''));
 const bodyText=document.body.innerText||'';
 const options=[...document.querySelectorAll('button,a,[role=button]')].map((x,i)=>({i,tag:x.tagName,text:(x.innerText||'').trim().slice(0,100),aria:x.getAttribute('aria-label'),outerHTML:x.outerHTML.slice(0,700)})).filter(x=>/تحميل المزيد|load more|المزيد|more/i.test(x.text+" "+x.aria)).slice(-25);
 const cards=[...document.querySelectorAll('h3,h4,h5,h6,a,strong,span,p')].filter(x=>/^(A[0-9]{1,3}|[0-9]{1,2}\/[0-9]{1,2})$/.test((x.innerText||'').trim()) && x.children.length===0).slice(0,90).map(x=>({code:(x.innerText||'').trim(),anchorHTML:x.outerHTML.slice(0,500),parentHTML:x.parentElement?.parentElement?.outerHTML.slice(0,2600),parentText:x.parentElement?.parentElement?.innerText.slice(0,350)}));
 return {url:location.href,title:document.title,has_section:!!section,buttons:options,cards,body_length:bodyText.length,body_text:bodyText.slice(0,110000),visible_links:[...document.querySelectorAll('a[href]')].filter(x=>/\/listings\/\d+/.test(x.href)&&!/(?:email|phone)/.test(x.href)).map(x=>({text:x.innerText.trim().slice(0,110),url:x.href})).slice(0,90)};
}"""
async def main():
    result={"schema":"SAE_MENACO_51_52_PUBLIC_LOAD_MORE_ORIGINAL_UNITS_READONLY_V1",
            "captured_utc":datetime.now(timezone.utc).isoformat(),
            "production_writes":0,"sources":[]}
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        for s in SOURCE:
            rec={"project_id":s["project_id"],"original_url":s["url"],"pages":[],"network":[],"errors":[]}
            result["sources"].append(rec)
            try:
                allowed,check=await asyncio.to_thread(check_robots,s["url"])
                rec["robots"]=check
                if not allowed:
                    rec["status"]="SOURCE_ACCESS_NOT_VERIFIED"
                    save(result);continue
            except Exception as exc:
                rec["status"]="ROBOTS_UNVERIFIED_"+type(exc).__name__
                save(result);continue
            page=await browser.new_page(user_agent=UA,viewport={"width":1400,"height":1100})
            blocked=False;responses=[]
            async def xhr(r):
                nonlocal blocked
                h=urlsplit(r.url).hostname
                if h and h.lower().removeprefix("www.")!="menaco.sa":return
                if r.status in (403,429):blocked=True;rec["errors"].append("PUBLISHER_HTTP_"+str(r.status));return
                if r.status!=200 or r.request.resource_type not in ("xhr","fetch"):return
                try:
                    raw=await r.body()
                    if len(raw)>5_000_000:return
                    v={"path":urlsplit(r.url).path,"method":r.request.method,"status":r.status,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"content_type":r.headers.get("content-type","")}
                    if b"A51" in raw or b"A50" in raw or b"A45" in raw or "json" in r.headers.get("content-type",""):
                        try:
                            j=json.loads(raw)
                            v["json_shape"]=list(j)[:15] if isinstance(j,dict) else str(type(j).__name__)
                            v["json_preview"]=json.dumps(j,ensure_ascii=False)[:14000]
                        except Exception:
                            v["sample_html"]=raw.decode("utf8","replace")[:7500]
                    if len(rec["network"])<90:rec["network"].append(v)
                except Exception as exc:rec["errors"].append("XHR_"+type(exc).__name__)
            page.on("response",lambda r:responses.append(asyncio.create_task(xhr(r))))
            try:
                p=await page.goto(s["url"],wait_until="domcontentloaded",timeout=45000)
                rec["http"]=p.status if p else None
                if p and p.status in (403,429):blocked=True
                if rec.get("http")==200 and not blocked:
                    await page.wait_for_timeout(1700)
                    # Project hides its per-unit cards behind explicit public
                    # "عرض الوحدات" display control. Opening this visible UI
                    # is required before its "تحميل المزيد" pagination exists.
                    tab=page.get_by_text("عرض الوحدات",exact=True)
                    rec["unit_tab_control_count"]=await tab.count()
                    if await tab.count() and await tab.first.is_visible():
                        try:
                            await tab.first.click(timeout=4500)
                            rec["unit_tab_clicked"]=True
                            await page.wait_for_timeout(2600)
                        except Exception as exc:
                            rec["errors"].append("UNIT_TAB_CLICK_"+type(exc).__name__)
                    previous=""
                    for step in range(30):
                        if blocked:break
                        state=await page.evaluate(EVAL)
                        state["pagination_stage"]=step
                        # Preserve visible codes and full original text, not the commercial headline unit count.
                        rec["pages"].append(state)
                        current=hashlib.sha256(state["body_text"].encode()).hexdigest()
                        if current==previous:break
                        previous=current
                        # A public 'Load More' button is part of ordinary UI, not an access bypass.
                        load=page.get_by_text(re.compile(r"^(?:تحميل المزيد|Load More)(?:\s|$)",re.I))
                        if not await load.count():break
                        enabled=False
                        for ix in range(min(4,await load.count())):
                            try:
                                if await load.nth(ix).is_visible() and await load.nth(ix).is_enabled():
                                    await load.nth(ix).click(timeout=4500)
                                    enabled=True
                                    break
                            except Exception as exc:
                                rec["errors"].append("CLICK_"+type(exc).__name__)
                        if not enabled:break
                        # Livewire updates asynchronously. A fixed sleep can
                        # accidentally record the loading overlay as the last
                        # source page, dropping later source codes.
                        oldcodes=len(normalized_original_cards(state["body_text"],s["project_id"]))
                        try:
                            await page.wait_for_function(
                                """(prev) => {
                                    let txt=document.body.innerText||'';
                                    let ix=txt.indexOf('الوحدات المتاحة');
                                    let end=txt.indexOf('خدمة العملاء المجانية',ix);
                                    if(ix<0) return false;
                                    let body=txt.slice(ix,end>ix?end:undefined);
                                    let match=body.match(/^(A[0-9]{1,3}|[0-9]{1,2}\\/[0-9]{1,2})$/gm)||[];
                                    return match.length>prev;
                                }""",arg=oldcodes,timeout=14000)
                        except Exception:
                            rec["errors"].append("LOAD_MORE_NO_NEW_CARD_WITHIN_TIMEOUT")
                            break
                        await page.wait_for_timeout(400)
                    rec["state"]="PUBLIC_PAGINATION_CAPTURED" if rec["pages"] else "NO_PUBLIC_PAGES"
                else:rec["state"]="HTTP_ERROR_STOP"
            except Exception as exc:
                rec["state"]="PAGE_ERROR_"+type(exc).__name__
                rec["errors"].append(str(exc)[:150])
            if responses:await asyncio.gather(*responses,return_exceptions=True)
            # Count OBSERVED DOM card code tokens without filling numbering gaps.
            codepat=CODES_51 if s["project_id"]=="PRJ-001802" else CODES_52
            codes=sorted({x["code"] for p in rec["pages"] for x in p.get("cards",[]) if codepat.fullmatch(x["code"])})
            rec["visible_exact_original_unit_code_candidates"]=codes
            rec["visible_code_count"]=len(codes)
            rec["original_source_physical_cards"] = normalized_original_cards(
                rec["pages"][-1]["body_text"], s["project_id"]) if rec["pages"] else []
            normalized_codes = {x["original_unit_code"] for x in rec["original_source_physical_cards"]}
            rec["normalized_codes_match_visible_dom"] = normalized_codes == set(codes)
            rec["source_card_qa_pass"] = bool(
                rec["normalized_codes_match_visible_dom"]
                and len(normalized_codes) == len(rec["original_source_physical_cards"])
                and all(x["qualifies_physical"] for x in rec["original_source_physical_cards"]))
            print("SAE_MENACO_RECONCILIATION_QA",json.dumps({
                "project":s["project_id"],"code_count":len(codes),
                "normalized_count":len(rec["original_source_physical_cards"]),
                "same_codes":rec["normalized_codes_match_visible_dom"],
                "qualified_count":sum(x["qualifies_physical"] for x in rec["original_source_physical_cards"]),
                "source_card_qa_pass":rec["source_card_qa_pass"],
                "holds":[x for x in rec["original_source_physical_cards"]
                         if not x["qualifies_physical"]][:5]
            },ensure_ascii=False),flush=True)
            if rec["source_card_qa_pass"]:
                for pos in range(0, len(rec["original_source_physical_cards"]), 12):
                    print("SAE_MENACO_EXACT_SOURCE_CHUNK", json.dumps({
                        "project_id": s["project_id"], "source_page": s["url"],
                        "source_captured_at_utc": result["captured_utc"],
                        "chunk": pos//12,
                        "cards": rec["original_source_physical_cards"][pos:pos+12]
                    }, ensure_ascii=False, separators=(",",":")), flush=True)
            rec["stage_count"]=len(rec["pages"])
            if rec["pages"]:
                start=rec["pages"][0]
                txt=start.get("body_text","")
                print("SAE_MENACO_DOM_DIAG",json.dumps({"project":s["project_id"],"title":start.get("title"),"buttons":start.get("buttons",[])[:8],"visible_links":start.get("visible_links",[])[:8],"text_start":txt[:8000],"text_end":txt[-12000:],"card_candidates":len(start.get("cards",[]))},ensure_ascii=False),flush=True)
            rec["blocked"]=blocked
            save(result)
            print("SAE_MENACO_SOURCE",json.dumps({"project":s["project_id"],"state":rec.get("state"),"http":rec.get("http"),"stage_count":rec["stage_count"],"original_code_count":rec["visible_code_count"],"codes_preview":codes[:70],"xhr_count":len(rec["network"]),"errors":rec["errors"][:5],"blocked":blocked},ensure_ascii=False),flush=True)
            await page.close()
            if blocked:result["global_stop"]="HTTP_403_OR_429";save(result);break
        await browser.close()
    save(result)
if __name__=="__main__":
    assert CODES_51.fullmatch("A51") and not CODES_51.fullmatch("A52-C")
    sample="الوحدات المتاحة\nA51\n1,964,000\nالرياض\n3 غرفة نوم\n3 حمام\n268.72 متر مربع\nللبيع\nخدمة العملاء المجانية"
    rows=normalized_original_cards(sample, "PRJ-001802")
    assert len(rows)==1 and rows[0]["published_price_sar"]==1964000 and rows[0]["qualifies_physical"]
    asyncio.run(main())
