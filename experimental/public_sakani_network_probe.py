#!/usr/bin/env python3
"""Publisher-only browser XHR shape reconnaissance. No Master access or individual-unit claims."""
import json, os, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher, StealthySession

URLS=[
  "https://sakani.sa/app/offplan-projects/35",
  "https://sakani.sa/app/offplan-projects/581",
]
UA="Open-source-Scrapling-Public-Demo/0.1"
OUTPUT=Path(os.environ["RUNNER_TEMP"])/"public-sakani-unit-api-shapes.json"
state={"schema":"PUBLIC_SAKANI_EXISTING_PUBLISHER_PROJECT_API_DISCOVERY_V1","captured_at_utc":datetime.now(timezone.utc).isoformat(),
       "publisher_urls":URLS,"results":[],"errors":[],"status":"STARTED",
       "private_mapping_loaded":False,"master_writes":0,"physical_units_imported":0}
def save():
    OUTPUT.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
def arrays(v, depth=0):
    if depth>3:return []
    if isinstance(v,list):
        v0=v[0] if v else None
        out=[{"length":len(v),"item_field_names":sorted(v0.keys())[:30] if isinstance(v0,dict) else []}]
        return out+arrays(v0,depth+1) if v0 is not None else out
    if isinstance(v,dict):
        out=[]
        for key,val in list(v.items())[:35]:
            if isinstance(val,(list,dict)):
                for node in arrays(val,depth+1):
                    out.append({"field":str(key)[:45], **node})
        return out[:30]
    return []
def safe_record(record):
    status=int(record.status)
    if status==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
    if status!=200:return None
    u=urlsplit(str(record.url))
    host=(u.hostname or "").lower().removeprefix("www.")
    if u.scheme!="https" or not (host=="sakani.sa" or host.endswith(".sakani.sa")):return None
    meta=getattr(record,"meta",{}) or {}
    if str(meta.get("resource_type") or "") not in ("xhr","fetch"):return None
    body=getattr(record,"body",b"")
    if not isinstance(body,bytes) or len(body)>1_048_576 or not body:return None
    try:obj=json.loads(body)
    except (ValueError,UnicodeError):return None
    structures=arrays(obj)
    if not structures:return None
    return {"host":host,"path":u.path,"method":str(getattr(record,"method","GET")).upper(),
            "response_keys":sorted(obj.keys())[:35] if isinstance(obj,dict) else [],
            "array_shapes":structures[:20],"raw_body_saved":False,"query_string_saved":False}
try:
    r=Fetcher.get("https://sakani.sa/robots.txt",retries=1,timeout=25,
                  follow_redirects="safe",headers={"User-Agent":UA})
    if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
    if int(r.status)!=200:raise RuntimeError("ROBOTS_NOT_AVAILABLE")
    rp=RobotFileParser()
    rp.parse(r.body.decode("utf-8","replace").splitlines())
    delay=max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
    with StealthySession(record_requests=True,max_recorded_requests=500) as browser:
        for url in URLS:
            if not rp.can_fetch(UA,url):
                state["errors"].append({"path":urlsplit(url).path,"error":"ROBOTS_DISALLOW"})
                save()
                continue
            time.sleep(delay)
            browser.network.clear()
            try:
                page=browser.fetch(url,network_idle=True)
                if int(page.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
                if int(page.status)!=200:raise ValueError("SOURCE_STATUS_"+str(page.status))
                network=list(browser.network.search(limit=None,include_static=False))
                seen=set()
                entries=[]
                for rec in network:
                    found=safe_record(rec)
                    if found is None:continue
                    key=(found["host"],found["path"],found["method"])
                    if key in seen:continue
                    seen.add(key)
                    entries.append(found)
                result={"publisher_path":urlsplit(url).path,"html_status":int(page.status),
                        "recorded_requests":len(network),"api_shapes":entries[:50],
                        "source_units_extracted":0}
                state["results"].append(result)
                print("API_DISCOVERY_RESULT "+json.dumps(result,ensure_ascii=False,separators=(",",":")))
            except RuntimeError as exc:
                if "HTTP_429_GLOBAL_STOP" in str(exc):raise
                state["errors"].append({"path":urlsplit(url).path,"error":str(exc)[:150]})
            except Exception as exc:
                state["errors"].append({"path":urlsplit(url).path,"error":type(exc).__name__+": "+str(exc)[:120]})
            save()
    state["status"]="COMPLETED_SHAPE_ONLY"
except Exception as exc:
    state["status"]="HALTED_429" if "HTTP_429_GLOBAL_STOP" in str(exc) else "STOPPED_WITH_ERROR"
    state["errors"].append({"error":type(exc).__name__+": "+str(exc)[:150]})
finally:
    save()
    print("DISCOVERY_FINAL "+json.dumps({"status":state["status"],"completed_pages":len(state["results"]),
      "api_candidates":sum(len(r["api_shapes"]) for r in state["results"]),
      "physical_units_extracted":0,"errors":state["errors"]},ensure_ascii=False,separators=(",",":")))
