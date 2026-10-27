#!/usr/bin/env python3
"""Public first-party project-card discovery using Scrapling; no private data.

The source URLs are publicly available publisher website project pages.
Fetch/parse only when robots.txt explicitly allows each path.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json, os, re, time, hashlib
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher, StealthySession

UA="Open-source-Scrapling-Public-Demo/0.1"
HOST="almajdiah.com"
URLS=[
  "https://almajdiah.com/projects/153",
  "https://almajdiah.com/projects/119",
  "https://almajdiah.com/projects/156",
  "https://almajdiah.com/projects/161",
  "https://almajdiah.com/projects/195",
  "https://almajdiah.com/projects/2",
]
output=Path(os.environ["RUNNER_TEMP"])/"public-original-publisher-source-shapes.json"
results=[]
def save():
    output.write_text(json.dumps({
        "schema":"PUBLIC_ORIGINAL_PUBLISHER_HTML_AND_XHR_SHAPES",
        "source":"public publisher data only, NO canonical IDs or user files",
        "raw_json_values_saved":False,"urls":results},ensure_ascii=False,indent=2),encoding="utf-8")

robots_url=f"https://{HOST}/robots.txt"
resp=Fetcher.get(robots_url,retries=1,timeout=25,follow_redirects="safe",
                 headers={"User-Agent":UA})
assert resp.status==200, f"robots not available {resp.status}"
rp=RobotFileParser()
rp.parse(resp.body.decode("utf8","replace").splitlines())
with StealthySession(record_requests=True,max_recorded_requests=500) as session:
    for url in URLS[:2]:
        item={"url":url,"observed_at_utc":datetime.now(timezone.utc).isoformat()}
        if not rp.can_fetch(UA,url):
            item["state"]="ROBOTS_DISALLOW"
            results.append(item);save();continue
        time.sleep(max(3,rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
        try:
            session.network.clear()
            page=session.fetch(url,network_idle=True)
            item["status"]=int(page.status)
            if page.status==429:
                item["state"]="HTTP_429_STOP";results.append(item);save();break
            item["html_bytes"]=len(page.body)
            item["html_sha256"]=hashlib.sha256(page.body).hexdigest()
            try:
                visible=str(page.get_all_text(ignore_tags=("script","style")))
            except (ValueError,TypeError,AttributeError):
                visible=page.body.decode("utf8","replace")
                visible=re.sub(r"<[^>]+>","\n",visible)
            compact=" ".join(visible.split())
            item["text_chars"]=len(compact)
            item["visible_excerpt"]=compact[:5500]
            item["network_responses"]=len(session.network.search(limit=None,include_static=False))
            item["network_inventory"]=[]
            for capture in session.network.search(limit=None,include_static=False)[:60]:
                capture_url=urlsplit(str(capture.url))
                item["network_inventory"].append({
                    "host":capture_url.hostname, "path":capture_url.path,
                    "status":int(capture.status),
                    "resource":str(capture.meta.get("resource_type")),
                    "bytes":len(capture.body),
                })
            item["html_clues"]={
                "has_next_data": b"__NEXT_DATA__" in page.body,
                "has_inertia": b"inertia" in page.body.lower(),
                "has_livewire": b"livewire" in page.body.lower(),
                "has_unit_number_token": b"unit_number" in page.body.lower(),
                "has_units_token": b"units" in page.body.lower(),
            }
            item["xhr_shapes"]=[]
            for net in session.network.search(limit=None,include_static=False):
                if net.status==429: item["state"]="XHR_HTTP_429_STOP";break
                if net.status!=200 or not net.body:continue
                parsed=urlsplit(str(net.url))
                if parsed.scheme!="https" or not ((parsed.hostname or "").removeprefix("www.")==HOST or (parsed.hostname or "").endswith("."+HOST)): continue
                try: data=json.loads(net.body)
                except (ValueError,TypeError,UnicodeError):continue
                arrays=[]
                if isinstance(data,dict):
                    for k,v in data.items():
                        if isinstance(v,list): arrays.append({"field":str(k),"count":len(v),"first_item_fields":list(v[0])[:20] if v and isinstance(v[0],dict) else []})
                if isinstance(data,list):arrays.append({"field":"$","count":len(data),"first_item_fields":list(data[0])[:20] if data and isinstance(data[0],dict) else []})
                if arrays or isinstance(data,dict):item["xhr_shapes"].append({"host":parsed.hostname,"path":parsed.path,"top_level_keys":sorted(str(k) for k in data)[:40] if isinstance(data,dict) else [],"arrays":arrays[:8]})
            if item.get("state")=="XHR_HTTP_429_STOP":results.append(item);save();break
            item["state"]="CAPTURED_NO_UNIT_COUNT_ASSUMED"
        except Exception as e:
            item["state"]="SOURCE_ERROR"
            item["error_type"]=type(e).__name__
        results.append(item)
        save()
        print(json.dumps({k:v for k,v in item.items() if k not in ("visible_excerpt",)},ensure_ascii=False))
save()
print(json.dumps({"summary_count":len(results),
                  "screens":results[:1],"saved":str(output)},ensure_ascii=False))
