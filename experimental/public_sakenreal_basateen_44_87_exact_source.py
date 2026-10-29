#!/usr/bin/env python3
"""Public broker source: exact numbered Jazan Al-Basateen plot table, read-only.
Capture only row codes, stated area, asking price, marketed status and street.
No contact data, no modelled rows, no writes to user database.
"""
import os,json,re,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit,quote
from bs4 import BeautifulSoup
from scrapling.fetchers import Fetcher

BASE="https://sakenreal.com"
URL=BASE+"/project/"+quote("مخطط-البساتين")+"/"
UA="Public-Saudi-Land-Inventory-Research/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"
def get(url):
    if urlsplit(url).hostname!="sakenreal.com":raise ValueError("offsite")
    r=Fetcher.get(url,retries=0,timeout=28,follow_redirects="safe",headers={"User-Agent":UA})
    if int(r.status)==429:raise RuntimeError("STOP_429")
    if int(r.status)==404 and url.endswith("/robots.txt"):return None
    if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
    if urlsplit(str(r.url)).hostname not in ("sakenreal.com","www.sakenreal.com"):raise RuntimeError("offsite_redirect")
    if not isinstance(r.body,bytes) or len(r.body)>7_000_000:raise RuntimeError("invalid body")
    return r.body.decode("utf8","replace")
def main():
    dest=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"jazan-basateen-exact-44-87-source-rows.json"
    out={"schema":"PUBLIC_SAKENREAL_JAZAN_BASATEEN_EXACT_PUBLISHER_TABLE_V1",
         "url":URL,"at":datetime.now(timezone.utc).isoformat(),
         "project_snapshot_rows":[],"target_44_87":[],"errors":[],"status":"STARTED",
         "canonical_writes":0}
    try:
        rp=RobotFileParser()
        robots=get(BASE+"/robots.txt")
        rp.parse(robots.splitlines() if robots is not None else [])
        if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
        time.sleep(max(2.5,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
        html=get(URL)
        soup=BeautifulSoup(html,"lxml")
        for table in soup.select("table"):
            for tr in table.select("tr"):
                columns=[x.get_text(" ",strip=True) for x in tr.select("td")]
                if not columns:continue
                first=columns[0].replace("٬","").replace(",","").strip()
                if not re.fullmatch(r"\d{1,3}",first):continue
                num=int(first)
                # Preserve only exact first eight publisher-rendered cells.
                record={"publisher_plot_code":first,"fields":columns[:8]}
                out["project_snapshot_rows"].append(record)
                if 44<=num<=87:out["target_44_87"].append(record)
        out["status"]="COMPLETE"
        if not out["target_44_87"]:
            out["warning"]="NO_ITEMIZED_ROWS_IN_PUBLIC_TABLE; no inferred codes"
    except Exception as e:
        out["status"]="STOP";out["errors"].append(str(e))
    finally:
        dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps({"status":out["status"],"source_table_rows":len(out["project_snapshot_rows"]),"target_44_87":len(out["target_44_87"]),"sample":out["target_44_87"][:3],"errors":out["errors"]},ensure_ascii=False))
    if out["status"]!="COMPLETE":raise SystemExit(1)
if __name__=="__main__":main()
