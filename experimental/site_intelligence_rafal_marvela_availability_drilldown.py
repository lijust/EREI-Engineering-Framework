#!/usr/bin/env python3
"""Rafal Marvela original public 'View Units Availability' modal, read-only.
Extract table structural facts and original displayed rows and controls;
no invented units, no user data, no form submissions or login.
"""
import os, json, re, time
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from scrapling.fetchers import Fetcher
from playwright.sync_api import sync_playwright

ROOT="https://www.rafal.com.sa"
URL=ROOT+"/communities/marvela"
UA="SAE-Site-Intelligence-Research/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"rafal-marvela-availability-modal-deep-intelligence.json"
d={"schema":"SAE_SOURCE_RECON_RAFAL_MARVELA_AVAILABILITY_MODAL_V1",
   "source":URL,"status":"STARTED","rows":[],"controls":{},"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
try:
    rr=Fetcher.get(ROOT+"/robots.txt",retries=0,timeout=25)
    if int(rr.status)==429:raise RuntimeError("STOP_429")
    rb=RobotFileParser()
    if int(rr.status)==200:rb.parse(rr.body.decode("utf8","replace").splitlines())
    elif int(rr.status)==404:rb.parse([])
    else:raise RuntimeError("ROBOTS_HTTP_"+str(rr.status))
    if not rb.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
    time.sleep(max(3,float(rb.crawl_delay(UA) or rb.crawl_delay("*") or 0)))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        try:
            page=browser.new_page()
            seen=[]
            page.on("response",lambda res:seen.append(res))
            nav=page.goto(URL,wait_until="domcontentloaded",timeout=40000)
            if nav is not None and nav.status==429:raise RuntimeError("STOP_429")
            page.wait_for_timeout(2000)
            btn=page.get_by_role("button",name=re.compile("View Units Availability",re.I))
            if btn.count()!=1 or btn.locator("xpath=ancestor::form").count()!=0:
                raise RuntimeError("NO_SAFE_EXACT_AVAILABILITY_BUTTON")
            btn.click(timeout=8000)
            page.wait_for_timeout(2800)
            d["tables"]=[]
            for ti,t in enumerate(page.locator("table").all()[:15]):
                trs=t.locator("tr")
                if not trs.count():continue
                thead=[[x.strip() for x in tr.locator("th").all_inner_texts()]
                    for tr in t.locator("thead tr").all()]
                tbody=[]
                for tr in t.locator("tbody tr").all()[:150]:
                    tbody.append([x.strip() for x in tr.locator("td").all_inner_texts()])
                d["tables"].append({"index":ti,"headers":thead,"row_count_visible":len(tbody),"rows":tbody,
                                    "id":t.get_attribute("id"),"classes":t.get_attribute("class")})
            d["controls"]["selects"]=[]
            for select in page.locator("select").all()[:30]:
                parent=select.locator("xpath=..")
                d["controls"]["selects"].append({
                    "id":select.get_attribute("id"),"name":select.get_attribute("name"),
                    "options":[{"value":x.get_attribute("value"),"text":x.inner_text()[:100]}
                        for x in select.locator("option").all()[:100]],
                    "nearby_text":parent.inner_text()[:260]})
            d["controls"]["buttons"]=[{"text":x.inner_text()[:100],
                "aria":x.get_attribute("aria-label"),"id":x.get_attribute("id"),
                "class":(x.get_attribute("class") or "")[:120]}
                for x in page.locator("button").all()[:100]]
            d["controls"]["pagination_texts"]=[x.inner_text()[:180] for x in page.locator(
                "[class*='pagination'], [class*='paginate'], [role='navigation']").all()[:50]]
            d["controls"]["modal_texts"]=[x.inner_text()[:2000] for x in page.locator(
                "[role='dialog'], .modal, [class*='Modal']").all()[:8]]
            d["controls"]["links_after"]=[{"href":x.get_attribute("href"),"text":x.inner_text()[:100]}
                 for x in page.locator("a[href]").all()[:400]
                 if re.search(r"unit|apartment|villa|flat|availability",x.get_attribute("href") or "",re.I)][:45]
            d["network"]=[]
            for res in seen:
                if res.status==429:raise RuntimeError("STOP_429")
                if res.request.resource_type not in ("xhr","fetch"):continue
                h=urlsplit(res.url).hostname or ""
                if not (h.endswith("rafal.com.sa") or h.endswith("rafal.sa")):continue
                d["network"].append({"url":urlsplit(res.url)._replace(query="",fragment="").geturl(),
                     "status":res.status,"method":res.request.method,"resource_type":res.request.resource_type})
            d["status"]="COMPLETE_READONLY_ORIGINAL_UI_MODAL"
            print("RAFA_MODAL_REPORT "+json.dumps({"tables":len(d["tables"]),
                   "table_rows":[t["row_count_visible"] for t in d["tables"]],
                   "selects":len(d["controls"]["selects"]),
                   "buttons":len(d["controls"]["buttons"]),
                   "first_rows":(d["tables"][0]["rows"][:3] if d["tables"] else []),
                   "net":len(d["network"])},ensure_ascii=False),flush=True)
        finally:browser.close()
except Exception as exc:
    d["status"]="STOP_429" if "STOP_429" in str(exc) else "SOURCE_ERROR"
    d["errors"].append(type(exc).__name__+": "+str(exc)[:280])
finally:
    save()
    print("RAFA_STATUS "+json.dumps({"status":d["status"],"errors":d["errors"]},ensure_ascii=False))
if d["status"]!="COMPLETE_READONLY_ORIGINAL_UI_MODAL":
    raise SystemExit(1)
