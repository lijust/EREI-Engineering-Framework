#!/usr/bin/env python3
"""Read-only source qualification for Sakani's two EXISTING SAE canonical projects.
No login, no bypasses, no inferred units, no database writes.
"""
import asyncio
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

SEEDS = [
    {"project_id": "PRJ-000900", "url": "https://sakani.sa/app/offplan-projects/35", "title": "Tilal Al Ghuroob Jeddah"},
    {"project_id": "PRJ-000451", "url": "https://sakani.sa/app/offplan-projects/36", "title": "Aali Jeddah"},
]
UA = "SAE-DB-source-study/1.0"
OUTPUT = Path("sae-sakani-35-36-public-structured-inventory.json")
CODE_KEYS = ("unitCode", "unit_code", "unitNumber", "unit_number", "unitNo", "propertyNumber", "property_number", "villaNumber", "plotNumber")
ALLOWED_FACT_KEYS = set(CODE_KEYS) | {"id", "area", "size", "price", "priceSar", "price_sar", "unitArea", "building", "buildingNo", "buildingNumber", "floor", "floorNo", "block", "blockNo", "model", "type", "status", "availability", "bedrooms", "bathrooms", "name", "title", "projectId"}
report = {"schema": "SAE_SAKANI_ORIGINAL_SOURCE_STUDY_ONLY_20261029", "captured_at_utc": datetime.now(timezone.utc).isoformat(), "production_writes": 0, "projects": []}
def save():
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def robots_ok(url):
    u = urlsplit(url)
    req = urllib.request.Request(f"{u.scheme}://{u.netloc}/robots.txt", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=18) as f:
        if f.status != 200: return False, f"ROBOTS_HTTP_{f.status}"
        body = f.read(200_001)
    if len(body) > 200000: return False, "ROBOTS_OVERSIZE"
    robot = RobotFileParser()
    robot.parse(body.decode("utf-8", "replace").splitlines())
    return robot.can_fetch(UA, url), "ROBOTS_CHECKED"
def get_arrays(obj, path="$", depth=0):
    if depth > 6: return []
    found = []
    if isinstance(obj, dict):
        for key, val in list(obj.items())[:70]:
            if isinstance(val, (list, dict)):
                found.extend(get_arrays(val, f"{path}.{key}", depth+1))
    elif isinstance(obj, list):
        if len(obj) >= 5 and all(isinstance(item, dict) for item in obj[:min(len(obj), 10)]):
            keys = sorted(set().union(*(x.keys() for x in obj[:min(5, len(obj))])))
            codes = []
            code_field = None
            for key in CODE_KEYS:
                seq = [str(x.get(key, "")).strip() for x in obj]
                if len(set(seq)) == len(seq) and all(z and z.lower() not in ("none", "null", "0") for z in seq):
                    code_field = key
                    codes = seq
                    break
            payload = {"path":path,"length":len(obj),"keys":keys[:50],"distinct_physical_code_field":code_field}
            if code_field:
                payload["coded_rows"] = [
                    {k: v for k, v in item.items() if k in ALLOWED_FACT_KEYS and isinstance(v, (str, int, float, bool, type(None)))}
                    for item in obj[:3000]
                ]
                payload["codes_sha256"] = hashlib.sha256("\n".join(codes).encode()).hexdigest()
            found.append(payload)
        for i, item in enumerate(obj[:2]):
            if isinstance(item, (list, dict)): found.extend(get_arrays(item, f"{path}[{i}]", depth+1))
    return found
async def inspect(seed, browser):
    item = {**seed,"responded":[],"api_shapes":[],"errors":[],"candidate_coded_records":0}
    try:
        allowed, check = await asyncio.to_thread(robots_ok, seed["url"])
        item.update(robots=check, robots_allowed=allowed)
        if not allowed: return item, False
    except Exception as exc:
        item.update(robots="ROBOTS_UNVERIFIED_"+type(exc).__name__,robots_allowed=False)
        return item, False
    page = await browser.new_page(user_agent=UA, viewport={"width": 1440, "height": 960})
    jobs = []
    blocked = False
    async def capture(response):
        nonlocal blocked
        host = urlsplit(response.url).hostname or ""
        if not (host == "sakani.sa" or host.endswith(".sakani.sa")): return
        if response.status == 429:
            blocked = True
            item["errors"].append("SAKANI_HTTP_429_STOP")
            return
        if response.status == 403:
            blocked = True
            item["errors"].append("SAKANI_HTTP_403_STOP")
            return
        if response.status != 200 or response.request.resource_type not in ("xhr", "fetch"): return
        if len(item["responded"]) >= 100: return
        ctype = response.headers.get("content-type","")
        try:
            body = await response.body()
            if not body or len(body) > 8_000_000: return
            u = urlsplit(response.url)
            meta = {"source_path":u.scheme+"://"+u.netloc+u.path, "method":response.request.method,"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body),"content_type":ctype}
            item["responded"].append(meta)
            if "json" in ctype.lower() or body[:1] in (b"{",b"["):
                try: doc=json.loads(body)
                except (ValueError,UnicodeError): return
                arr=get_arrays(doc)
                for a in arr:
                    if a.get("distinct_physical_code_field"):
                        item["candidate_coded_records"] += len(a["coded_rows"])
                    item["api_shapes"].append({"response":meta["source_path"],**a})
        except Exception as exc:
            item["errors"].append("RESPONSE_"+type(exc).__name__)
    page.on("response",lambda r:jobs.append(asyncio.create_task(capture(r))))
    try:
        r = await page.goto(seed["url"], wait_until="domcontentloaded",timeout=45000)
        item["http_status"] = r.status if r else None
        if r and r.status in (403,429): blocked=True
        if not blocked:
            await page.wait_for_timeout(6500)
            item["page_title"] = await page.title()
            item["public_unit_links"] = await page.locator("a[href*='/app/units/']").evaluate_all(
                "(a)=>[...new Set(a.map(x=>x.href))].slice(0,1500)")
            for selector in ("text=عرض الوحدات", "text=الوحدات", "text=View Units"):
                if blocked: break
                loc=page.locator(selector)
                try:
                    if await loc.count() and await loc.first.is_visible():
                        await loc.first.click(timeout=3500)
                        await page.wait_for_timeout(3500)
                        item["clicked"] = selector
                        item["public_unit_links_after_click"] = await page.locator("a[href*='/app/units/']").evaluate_all(
                            "(a)=>[...new Set(a.map(x=>x.href))].slice(0,1500)")
                        break
                except Exception as exc: item["errors"].append("CLICK_"+type(exc).__name__)
            item["final_url"] = page.url
    except Exception as exc:
        item["errors"].append("PAGE_"+type(exc).__name__+":"+str(exc)[:100])
    if jobs: await asyncio.gather(*jobs,return_exceptions=True)
    await page.close()
    return item, blocked
async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for seed in SEEDS:
            row,blocked=await inspect(seed,browser)
            report["projects"].append(row)
            save()
            print(json.dumps({"project_id":seed["project_id"],"http_status":row.get("http_status"),"robots":row.get("robots"),"candidate_coded_records":row.get("candidate_coded_records"),"xhr":len(row["responded"]),"errors":row["errors"][:5]},ensure_ascii=False),flush=True)
            if blocked:
                report["stop_reason"]="HTTP_403_OR_429_ACCESS_CONTROL"
                save()
                break
        await browser.close()
    save()
if __name__=="__main__":
    assert get_arrays({"count":315})==[]
    assert not any(x.get("distinct_physical_code_field") for x in get_arrays({"models":[{"name":"A"} for _ in range(10)]}))
    assert get_arrays({"data":[{"unitNumber":str(i),"price":1} for i in range(25)]})[0]["distinct_physical_code_field"]=="unitNumber"
    asyncio.run(main())
