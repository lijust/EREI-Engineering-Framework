#!/usr/bin/env python3
"""Public Retal Verse inventory structure probe, no unit or customer downloads.

Robots-gated read only; captures ONLY names of public asset paths and structural
API hints from anonymous HTML and JS, never form/cookie/PII.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json, re, time
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

HOST="verse.retal.com.sa"
BASE="https://"+HOST
UA="Source-Public-Structure-Research/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"

class HTML(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        kv=dict(attrs)
        if tag=="script" and kv.get("src"):self.scripts.append(kv["src"])
        if tag in ("a","link") and kv.get("href"):self.links.append(kv["href"])

def get(url):
    from scrapling.fetchers import Fetcher
    p=urlparse(url)
    if p.scheme!="https" or p.hostname!=HOST or p.username or p.password:
        raise ValueError("Off-domain access rejected")
    r=Fetcher.get(url,timeout=28,retries=0,follow_redirects="safe",headers={"User-Agent":UA})
    if int(r.status)==429:raise RuntimeError("STOP_429")
    if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
    if urlparse(str(r.url)).hostname!=HOST:raise RuntimeError("Off-host redirect")
    if not isinstance(r.body,bytes) or not 0<len(r.body)<8_000_000:raise RuntimeError("No/oversized public response")
    return r.body.decode("utf-8",errors="replace")

def main():
    import os
    dest=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"retal-verse-structural-public-api-hints.json"
    state={"schema":"PUBLIC_RETAL_VERSE_SOURCE_STRUCTURE_V1","origin":BASE,
        "html_links":[],"js_asset_paths":[],"potential_api_route_hints":[],
        "status":"STARTED","canonical_writes":0}
    try:
        robots=get(BASE+"/robots.txt")
        rule=RobotFileParser();rule.parse(robots.splitlines())
        url=BASE+"/"
        if not rule.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW")
        time.sleep(2.5)
        html=get(url)
        tags=HTML();tags.feed(html)
        state["html_length"]=len(html)
        state["html_links"]=[urlparse(urljoin(BASE,href)).path for href in tags.links[:70]]
        js_assets=[]
        for href in tags.scripts:
            target=urljoin(BASE,href)
            q=urlparse(target)
            if q.hostname==HOST and q.path.endswith(".js") and target not in js_assets:
                js_assets.append(target)
        state["js_asset_paths"]=[urlparse(x).path for x in js_assets[:40]]
        for target in js_assets[:6]:
            if not rule.can_fetch(UA,target):continue
            time.sleep(2.5)
            try:
                body=get(target)
                found=sorted(set(
                    re.findall(r'[/]["\x27]*(?:api|v1|v2|properties|units|inventory)[-/a-zA-Z0-9_./?=%]{3,150}',body,re.I)
                ))[:100]
                state["potential_api_route_hints"].append(
                    {"asset":urlparse(target).path,"size":len(body),"route_snippets":found})
            except Exception as ex:
                if str(ex)=="STOP_429":raise
                state.setdefault("errors",[]).append({"asset":urlparse(target).path,"error":str(ex)[:100]})
        state["status"]="COMPLETE_PUBLIC_SOURCE_ONLY"
    except Exception as e:
        state["status"]="STOP_"+type(e).__name__
        state.setdefault("errors",[]).append(str(e)[:150])
    finally:
        dest.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps({"status":state["status"],"assets":len(state["js_asset_paths"]),
                          "hints":len(state["potential_api_route_hints"]),
                          "out":str(dest)},ensure_ascii=False))
    if state["status"]!="COMPLETE_PUBLIC_SOURCE_ONLY":raise SystemExit(1)
if __name__=="__main__":main()
