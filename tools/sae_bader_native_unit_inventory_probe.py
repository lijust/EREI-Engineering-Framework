#!/usr/bin/env python3
"""SAE-DB | Existing Saraya Al Bader first-party inventory deep XHR discovery.

Read-only source intelligence: only official publicly linked interactive map.
Never infer physical units from project totals, model counts or HTML plan numbers.
No login, CAPTCHA, authentication, access bypass, or canonical Google Sheets write.
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

PAGE = "https://saraya-al-bader.darwaemaar.com/"
PUBLISHER = "darwaemaar.com"
PROJECT_ID = "PRJ-001090"
OUT = Path("sae-bader-original-unit-discovery.json")
UA = "SAE-DB-original-public-inventory/1.0"
CODE_FIELDS = ("unitCode", "unit_code", "unitNumber", "unit_number",
               "unitNo", "villaNumber", "plotNumber", "landNumber",
               "apartmentNumber", "propertyNumber")
BUILDING_FIELDS = ("building", "buildingNo", "block", "blockNo", "buildingNumber")
PUBLIC_FACT = set(CODE_FIELDS + BUILDING_FIELDS) | {
    "id", "price", "priceSar", "price_sar", "area", "size", "landArea",
    "houseArea", "projectId", "project_id", "phase", "status", "model",
    "floor", "type", "bedrooms", "bathrooms"
}
result = {
    "schema": "SAE_PUBLIC_EXISTING_PRJ_001090_SARAYA_AL_BADER_NATIVE_SOURCE_V1",
    "project_id": PROJECT_ID, "source_url": PAGE,
    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "site_only": True, "master_writes": 0, "api_shapes": [],
    "candidate_unit_rows": [], "response_metadata": [], "errors": []
}

class AccessStop(Exception):
    pass

def source_host(host):
    return bool(host and (host == PUBLISHER or host.endswith("." + PUBLISHER)))

def check_robots(target):
    p = urlsplit(target)
    if p.scheme != "https" or not source_host(p.hostname):
        return False, "UNTRUSTED_HOST"
    u = "https://" + p.hostname + "/robots.txt"
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=18) as f:
        if f.status == 429:
            raise AccessStop("ROBOTS_HTTP_429")
        if f.status != 200:
            return False, "ROBOTS_HTTP_" + str(f.status)
        body = f.read(180001)
    if len(body) > 180000 or not body:
        return False, "ROBOTS_INVALID"
    rp = RobotFileParser()
    rp.parse(body.decode("utf-8", "replace").splitlines())
    return rp.can_fetch(UA, target), "ROBOTS_CHECKED"

def discover_arrays(obj, path="$", depth=0):
    if depth > 7:
        return []
    found = []
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:80]:
            if isinstance(v, (dict, list)):
                found.extend(discover_arrays(v, path + "." + str(k), depth + 1))
    if isinstance(obj, list):
        if len(obj) >= 3 and all(isinstance(o, dict) for o in obj[:min(8, len(obj))]):
            keys = sorted(set().union(*(o.keys() for o in obj[:min(8, len(obj))])))
            code = next((k for k in CODE_FIELDS if k in keys and
                         all(str(x.get(k) or "").strip() not in ("", "0")
                             for x in obj) and
                         len(set(str(x[k]).strip() for x in obj)) == len(obj)), None)
            item = {"json_path": path, "length": len(obj), "keys": keys[:60],
                    "unique_unit_code_field": code}
            if code:
                # A model array or a foreign project's records do not qualify
                # unless a project/context identity is separately verified.
                item["coded_rows"] = [
                    {k: v for k, v in x.items() if k in PUBLIC_FACT and
                     (v is None or isinstance(v, (str, int, float, bool)))}
                    for x in obj[:4500]
                ]
            found.append(item)
        for i, o in enumerate(obj[:2]):
            if isinstance(o, (list, dict)):
                found.extend(discover_arrays(o, path + "[" + str(i) + "]", depth + 1))
    return found[:120]

def save():
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

async def main():
    try:
        allowed, reason = await asyncio.to_thread(check_robots, PAGE)
    except AccessStop as e:
        result["status"] = str(e)
        save()
        return
    except Exception as e:
        result["status"] = "ROBOTS_UNVERIFIED_" + type(e).__name__
        save()
        return
    result["robots"] = reason
    if not allowed:
        result["status"] = "ROBOTS_DISALLOW"
        save()
        return

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=UA, viewport={"width": 1360, "height": 900})
        tasks = []
        blocked = False
        seen_sha = set()
        async def capture(response):
            nonlocal blocked
            parsed = urlsplit(response.url)
            if not source_host(parsed.hostname):
                return
            if response.status in (403, 429):
                blocked = True
                result["errors"].append("SOURCE_STOP_HTTP_" + str(response.status))
                return
            if blocked or response.status != 200:
                return
            if response.request.resource_type not in ("xhr", "fetch"):
                return
            try:
                # Follow published browser requests only; do not guess APIs.
                allow, why = await asyncio.to_thread(check_robots, response.url)
                if not allow:
                    result["errors"].append("XHR_ROBOTS_DENY_OR_UNVERIFIED")
                    return
                body = await response.body()
                if not body or len(body) > 6_000_000:
                    return
                sha = hashlib.sha256(body).hexdigest()
                if sha in seen_sha or len(result["response_metadata"]) >= 80:
                    return
                seen_sha.add(sha)
                meta = {"host": parsed.hostname, "path": parsed.path,
                        "method": response.request.method, "status": response.status,
                        "sha256": sha, "bytes": len(body),
                        "content_type": response.headers.get("content-type", "")}
                result["response_metadata"].append(meta)
                try:
                    doc = json.loads(body)
                except (UnicodeError, ValueError):
                    return
                for array in discover_arrays(doc):
                    coded = array.pop("coded_rows", None)
                    result["api_shapes"].append({**meta, **array})
                    if coded:
                        # Source identity is still PENDING: original app content may
                        # mix project-specific and multi-project inventory.
                        result["candidate_unit_rows"].append(
                            {"source_response_sha256": sha,
                             "source_path": parsed.path, "json_path": array["json_path"],
                             "unit_code_field": array["unique_unit_code_field"],
                             "source_project_identity": "UNVERIFIED_HOLD",
                             "records": coded})
            except Exception as e:
                result["errors"].append("CAPTURE_" + type(e).__name__)

        page.on("response", lambda r: tasks.append(asyncio.create_task(capture(r))))
        try:
            response = await page.goto(PAGE, wait_until="domcontentloaded", timeout=45000)
            result["page_http"] = response.status if response else None
            if response and response.status in (403,429):
                blocked = True
            if not blocked:
                await page.wait_for_timeout(4500)
                result["page_title"] = await page.title()
                result["page_header"] = (await page.locator("body").inner_text())[:2500]
                # Read visible navigation; only interact with actual labels.
                result["public_links"] = (await page.locator("a[href]").evaluate_all(
                    "(a)=>a.slice(0,150).map(x=>({text:(x.innerText||'').slice(0,80),url:x.href}))"))[:150]
                for label in ("عرض الوحدات", "الوحدات", "View Units", "Units", "المخطط"):
                    if blocked:
                        break
                    button = page.get_by_text(label, exact=True)
                    try:
                        if await button.count() and await button.first.is_visible():
                            await button.first.click(timeout=2500)
                            result["clicked"] = label
                            await page.wait_for_timeout(2800)
                            break
                    except Exception as e:
                        result["errors"].append("CLICK_" + type(e).__name__)
                result["after_interaction_url"] = page.url
        except Exception as e:
            result["errors"].append("PAGE_" + type(e).__name__ + ": " + str(e)[:130])
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        result["status"] = ("HTTP_403_OR_429_STOP" if blocked else
                            "SOURCE_ONLY_NEEDS_CROSSWALK" if result["candidate_unit_rows"] else
                            "NO_PUBLIC_CODED_SOURCE_FOUND")
        await browser.close()
        save()
    print(json.dumps({
        "status": result.get("status"), "http": result.get("page_http"),
        "xhr": len(result["response_metadata"]),
        "arrays": len(result["api_shapes"]),
        "candidate_arrays_held": len(result["candidate_unit_rows"]),
        "candidate_rows_held": sum(len(x["records"]) for x in result["candidate_unit_rows"]),
        "errors": result["errors"][:8], "master_writes": 0
    }, ensure_ascii=False), flush=True)

def self_test():
    assert source_host("saraya-al-bader.darwaemaar.com")
    assert not source_host("fake-darwaemaar.com")
    assert discover_arrays({"total": 634}) == []
    arr = discover_arrays({"units": [{"unitNumber": str(i+1), "price": i} for i in range(100)]})
    assert len(arr) == 1 and len(arr[0]["coded_rows"]) == 100
    arr = discover_arrays({"models": [{"model": "A"} for _ in range(15)]})
    assert arr[0]["unique_unit_code_field"] is None
    print("SAE_BADER_LOCAL_TESTS_PASS", flush=True)

if __name__ == "__main__":
    self_test()
    asyncio.run(main())
