#!/usr/bin/env python3
"""SAE-DB: multi-origin existing-project source inventory intelligence, READ ONLY.

One hosted run examines multiple publisher sites; records original per-unit table
rows and same-origin API shapes with strict access gates. Coded records are ONLY
research candidates, not canonical physical units. Never synthesize project totals.
"""
from __future__ import annotations
import asyncio, argparse, hashlib, json, re, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

UA = "SAE-DB-source-research/1.0"
STOP_CODES = {403, 429}
CODE_FIELDS = ("unitCode", "unit_code", "unitNumber", "unit_number",
               "unitNo", "villaNumber", "plotNumber", "landNumber", "apartmentNo",
               "propertyNumber", "apartmentNumber")
BUILDING_FIELDS = ("building", "buildingNo", "buildingNumber", "block", "blockNo")
FACT_FIELDS = set(CODE_FIELDS + BUILDING_FIELDS) | {
    "projectId", "project_id", "projectNumber", "price", "priceSar", "price_sar",
    "area", "size", "houseArea", "landArea", "floor", "status", "availability",
    "phase", "type", "bedrooms", "bathrooms", "roomCount", "model"
}
MAX_RESPONSE_BYTES = 3_000_000
MAX_ORIGIN_RECORDS = 80
CAPTURE_LIMIT = 2500
HOST_STOP = object()

def host(url: str) -> str:
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Only public HTTPS publisher origin URLs")
    return p.hostname.lower().removeprefix("www.")

def check_robots(url: str, opener=None):
    original = urlsplit(url)
    domain = host(url)
    robots_url = "https://" + original.hostname + "/robots.txt"
    if opener is None:
        opener = lambda r: urllib.request.urlopen(
            urllib.request.Request(r, headers={"User-Agent": UA}), timeout=15)
    try:
        with opener(robots_url) as response:
            if response.status in STOP_CODES: return False, "ROBOTS_HTTP_"+str(response.status)
            if response.status != 200: return False, "ROBOTS_HTTP_"+str(response.status)
            body = response.read(180001)
    except Exception as exc:
        code = getattr(exc, "code", None)
        return False, ("ROBOTS_HTTP_"+str(code) if code is not None
                       else "ROBOTS_UNVERIFIED_"+type(exc).__name__)
    if not body or len(body)>180000: return False, "ROBOTS_INVALID"
    rp=RobotFileParser()
    rp.parse(body.decode("utf-8","replace").splitlines())
    return rp.can_fetch(UA,url), "ROBOTS_CHECKED"

def api_arrays(obj, path="$", depth=0):
    """Only capture first-party code-looking arrays; no id-only/listing totals."""
    if depth>6:return []
    out=[]
    if isinstance(obj,dict):
        for k,v in list(obj.items())[:80]:
            if isinstance(v,(dict,list)):
                out.extend(api_arrays(v,path+"."+str(k),depth+1))
    elif isinstance(obj,list):
        if len(obj)>=2 and all(isinstance(x,dict) for x in obj[:min(8,len(obj))]):
            keys=sorted(set().union(*(x.keys() for x in obj[:min(10,len(obj))])))
            identity=next((k for k in CODE_FIELDS if k in keys
                           and all(str(x.get(k) or "").strip() not in ("","0","None") for x in obj)
                           and len({str(x[k]).strip() for x in obj})==len(obj)),None)
            item={"json_path":path,"source_array_length":len(obj),"field_names":keys[:45],
                  "original_unit_code_field":identity}
            if identity:
                item["candidate_rows"]=[{k:v for k,v in row.items()
                                      if k in FACT_FIELDS and (v is None or isinstance(v,(str,int,float,bool)))}
                                      for row in obj[:CAPTURE_LIMIT]]
            out.append(item)
        for i,x in enumerate(obj[:2]):
            if isinstance(x,(dict,list)):out.extend(api_arrays(x,path+"["+str(i)+"]",depth+1))
    return out[:100]

def table_is_unit(header: str):
    norm=" ".join(header.lower().split())
    return bool(("رقم الوحدة" in norm or "unit number" in norm or "unit no" in norm)
                and ("السعر" in norm or "المساحة" in norm or "status" in norm
                     or "price" in norm or "area" in norm))

def sanitize_table(raw: list):
    out=[]
    for item in raw[:30]:
        headers=item.get("headers") or []
        if not table_is_unit(" ".join(headers)):continue
        rows=[]
        for raw_row in (item.get("rows") or [])[:CAPTURE_LIMIT]:
            row=[str(x).strip()[:250] for x in raw_row[:20]]
            if row:rows.append(row)
        out.append({"headers":[str(x)[:110] for x in headers[:20]],
                    "source_table_rows":len(rows),
                    "rows":rows})
    return out

def read_manifest(file):
    j=json.loads(Path(file).read_text(encoding="utf-8"))
    arr=j["projects"]
    if not isinstance(arr,list) or not 1<=len(arr)<=45: raise ValueError("Manifest size must be 1..45")
    seen=set()
    for p in arr:
        if not re.fullmatch(r"PRJ-\d{6}",p["project_id"]):
            raise ValueError("Invalid canonical id")
        if not p.get("existing_canonical"): raise ValueError("Only existing project IDs")
        h=host(p["url"])
        key=(p["project_id"],p["url"])
        if key in seen:raise ValueError("Duplicate project URL pair")
        seen.add(key)
    return arr

EVAL_DOM = r"""() => {
 const all=[...document.querySelectorAll("table")].slice(0,35);
 const ts=all.map(t=>({
   headers:[...(t.querySelector("thead")||t.querySelector("tr")||t).querySelectorAll("th,td")].map(x=>x.innerText.trim()).slice(0,20),
   rows:[...t.querySelectorAll("tr")].slice(1,2501)
      .map(tr=>[...tr.querySelectorAll("td,th")].map(x=>x.innerText.trim().slice(0,250)).slice(0,20))
 }));
 const labels=[...document.querySelectorAll("button,a")].map(x=>({
   label:(x.innerText||x.getAttribute("aria-label")||"").trim().slice(0,90),
   href:x.href||null
 })).filter(x=>/تحميل المزيد|عرض الوحدات|all units|view units|show more|unit list|page\s*[2-9]/i.test(x.label))
 .slice(0,50);
 return {title:document.title,tables:ts,unit_navigation:labels,body_sha_text:(document.body.innerText||"").slice(0,250)};
}"""

def save(path,data):
    t=Path(str(path)+".tmp")
    t.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    t.replace(path)

async def run(manifest, outfile, *, delay=2.5):
    if delay<2:raise ValueError(">=2 seconds source delay")
    from playwright.async_api import async_playwright
    info={"schema":"SAE_EXISTING_MULTISOURCE_ITEMIZED_DEEP_STUDY_V1",
          "observed_at_utc":datetime.now(timezone.utc).isoformat(),
          "scope":"EXISTING_ONLY", "canonical_writes":0,"sources":[],"stop":None}
    blocked_hosts=set()
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for source in manifest:
            h=host(source["url"])
            rec={"project_id":source["project_id"],"page_url":source["url"],
                 "origin":h,"state":"STARTED","api_arrays":[],"original_unit_tables":[],
                 "xhr_shapes":[],"errors":[],"observed_at_utc":datetime.now(timezone.utc).isoformat()}
            info["sources"].append(rec)
            if h in blocked_hosts:
                rec["state"]="ORIGIN_BLOCKED_PREVIOUS"
                save(outfile,info);continue
            allowed,rs=await asyncio.to_thread(check_robots,source["url"])
            rec["robots"]=rs
            if rs == "ROBOTS_HTTP_429":
                rec["state"]="HTTP_429_GLOBAL_STOP"
                info["stop"]="HTTP_429"
                save(outfile, info)
                break
            if not allowed:
                rec["state"]="ACCESS_NOT_VERIFIED_OR_DISALLOWED"
                blocked_hosts.add(h)
                save(outfile,info);continue
            page=await browser.new_page(user_agent=UA,viewport={"width":1280,"height":900})
            tasks=[]
            stop_event=asyncio.Event()
            seen=set()
            async def inspect_response(r):
                target=urlsplit(r.url)
                rh=(target.hostname or "").lower().removeprefix("www.") if target.scheme=="https" else ""
                if rh!=h:return
                if r.status in STOP_CODES:
                    stop_event.set()
                    rec["errors"].append("ORIGIN_HTTP_"+str(r.status))
                    return
                if r.status!=200 or r.request.resource_type not in ("xhr","fetch"):return
                path=target.path
                if not (path and len(rec["xhr_shapes"])<MAX_ORIGIN_RECORDS):return
                try:
                    raw=await r.body()
                    if not raw or len(raw)>MAX_RESPONSE_BYTES:return
                    sha=hashlib.sha256(raw).hexdigest()
                    if sha in seen:return
                    seen.add(sha)
                    x={"path":path,"method":r.request.method,"bytes":len(raw),
                       "sha256":sha,"status":r.status}
                    rec["xhr_shapes"].append(x)
                    try:js=json.loads(raw)
                    except (ValueError,UnicodeError):return
                    for arr in api_arrays(js):
                        encoded=arr.pop("candidate_rows",None)
                        rec["api_arrays"].append({**x,**arr})
                        if encoded is not None:
                            rec.setdefault("original_code_candidates_UNVERIFIED",[]).append(
                              {"response_sha256":sha,"path":path,
                               "field":arr["original_unit_code_field"],
                               "project_scope":"NOT_VERIFIED_HOLD",
                               "rows":encoded})
                except Exception as exc:
                    rec["errors"].append("XHR_"+type(exc).__name__)
            page.on("response",lambda r:tasks.append(asyncio.create_task(inspect_response(r))))
            try:
                await asyncio.sleep(delay)
                resp=await page.goto(source["url"],wait_until="domcontentloaded",timeout=28000)
                rec["http"]=resp.status if resp else None
                if resp and resp.status in STOP_CODES:stop_event.set()
                if not stop_event.is_set() and resp and resp.status==200:
                    await page.wait_for_timeout(2500)
                    dom=await page.evaluate(EVAL_DOM)
                    rec["page_title"]=dom.get("title")
                    rec["original_unit_tables"]=sanitize_table(dom.get("tables",[]))
                    rec["unit_navigation"]=dom.get("unit_navigation",[])[:20]
                    rec["table_count_total"]=len(dom.get("tables",[]))
                    rec["original_unit_table_history"] = [{"stage": "initial", "tables":rec["original_unit_tables"]}]
                    # Only click explicitly labeled public *unit-list pagination*.
                    # Do not interact with sign-in, lead-gen, reservations or unnumbered global controls.
                    if rec["original_unit_tables"] and not stop_event.is_set():
                        prior_fp=hashlib.sha256(json.dumps(rec["original_unit_tables"],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                        for step in range(1,9):
                            if stop_event.is_set():break
                            loc=page.get_by_role("button",name=re.compile(r"^(?:تحميل المزيد|عرض المزيد|Load more|Show more)$",re.I))
                            if not await loc.count():break
                            button=loc.first
                            if not await button.is_visible() or not await button.is_enabled():break
                            try:
                                await button.click(timeout=2500)
                                await page.wait_for_timeout(1400)
                                if stop_event.is_set():break
                                next_dom=await page.evaluate(EVAL_DOM)
                                tables=sanitize_table(next_dom.get("tables",[]))
                                next_fp=hashlib.sha256(json.dumps(tables,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                                if next_fp==prior_fp:break
                                rec["original_unit_table_history"].append({"stage":"load_more_"+str(step),"tables":tables})
                                prior_fp=next_fp
                            except Exception as exc:
                                rec["errors"].append("PAGINATION_"+type(exc).__name__)
                                break
                rec["state"]="ORIGIN_ACCESS_STOP" if stop_event.is_set() else ("SITE_VISITED" if rec.get("http")==200 else "HTTP_OR_PAGE_UNAVAILABLE")
            except Exception as exc:
                rec["state"]="PAGE_ERROR"
                rec["errors"].append(type(exc).__name__)
            if tasks:await asyncio.gather(*tasks,return_exceptions=True)
            await page.close()
            if stop_event.is_set():
                blocked_hosts.add(h)
                if "429" in " ".join(rec["errors"]):
                    rec["state"]="HTTP_429_GLOBAL_STOP"
                    info["stop"]="HTTP_429"
                    save(outfile,info)
                    break
            rec["original_numbered_table_rows_held"]=sum(x["source_table_rows"] for x in rec["original_unit_tables"])
            rec["original_numbered_api_rows_held"]=sum(len(x["rows"]) for x in rec.get("original_code_candidates_UNVERIFIED",[]))
            print(json.dumps({k:rec.get(k) for k in
                ("project_id","state","robots","http","original_numbered_table_rows_held",
                 "original_numbered_api_rows_held")},ensure_ascii=False),flush=True)
            save(outfile,info)
        await browser.close()
    info["run_status"]="COMPLETE_SOURCE_ONLY" if not info["stop"] else info["stop"]
    save(outfile,info)
    return info

def tests():
    assert table_is_unit("رقم الوحدة \t المساحة \t السعر")
    assert table_is_unit("Unit Number Price Status")
    assert not table_is_unit("Keystroke Action")
    assert not table_is_unit("Number Models Total Units")
    assert api_arrays({"units":[{"unitCode":str(k),"area":100} for k in range(9)]})[0]["source_array_length"]==9
    assert api_arrays({"models":[{"model":"A"} for _ in range(9)]})[0]["original_unit_code_field"] is None
    assert not api_arrays({"total_units":4000})
    assert sanitize_table([{"headers":["Keystroke","Action"],"rows":[["a","b"]]}])==[]
    assert len(sanitize_table([{"headers":["رقم الوحدة","السعر"],"rows":[["A1","10"],["A2","20"]]}])[0]["rows"])==2
    assert host("https://www.senanrealestate.sa/projects/123")=="senanrealestate.sa"
    try:host("http://unsafe.test")
    except ValueError:pass
    else:raise AssertionError("HTTP insecure")
    print("SAE_MULTISOURCE_OFFLINE_TESTS_PASS")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,default=Path("tools/sae_existing_frontier_batch_20261029.json"))
    ap.add_argument("--output",type=Path,default=Path("sae-existing-frontier-batch-original.json"))
    ap.add_argument("--delay",type=float,default=2.5)
    args=ap.parse_args()
    tests()
    data=read_manifest(args.manifest)
    asyncio.run(run(data,args.output,delay=args.delay))
