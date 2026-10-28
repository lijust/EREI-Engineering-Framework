#!/usr/bin/env python3
"""Source-only multi-publisher Scrapling first-party UNIT table discovery (no private DB IDs).
In this public experimental runner only PUBLIC original publisher URLs are included.
No canonical IDs, project counts, developer identities, auth tokens, or private data.
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LX

URLS = [
  "https://koohejidevelopment.sa/community/rewan-al-ruba/",
  "https://koohejidevelopment.sa/community/vellano/",
  "https://www.rafal.com.sa/ar/communities/marvela",
  "https://www.rafal.com.sa/ar/communities/burj-rafal",
  "https://retal.com.sa/en/properties/nesaj-sadayem/",
  "https://retal.com.sa/en/properties/nesaj-town-al-hasa/",
  "https://retal.com.sa/en/properties/nesaj-al-asala/",
  "https://retal.com.sa/en/properties/rejan-hills/",
  "https://koohejidevelopment.sa/community/lavira/",
  "https://www.rafal.com.sa/ar/communities/alegria",
  "https://koohejidevelopment.sa/community/belgravia/",
  "https://koohejidevelopment.sa/community/flamant/",
  "https://www.rafal.com.sa/communities/rafal-residence",
  "https://www.rafal.com.sa/ar/communities/blncyah",
  "https://retal.com.sa/en/properties/retal-rise/",
  "https://rasf.sa/listing/dh-yrd-21",
  "https://aswar.com.sa/our-projects/aswar-villas-01",
  "https://aswar.com.sa/our-projects/aswar-villas-02",
  "https://retal.com.sa/en/properties/nobu-2/",
  "https://retal.com.sa/en/properties/ayala-al-muhammadiyah/",
  "https://retal.com.sa/en/properties/ayala-al-nakheel/",
  "https://alhazem.com.sa/en/project/alhazem-residence/",
  "https://aswar.com.sa/our-projects/turquoise",
  "https://aswar.com.sa/our-projects/root",
  "https://alhazem.com.sa/project/جوهرة-الحزم/",
  "https://www.rafal.com.sa/communities/pavilions",
  "https://naf.com.sa/projects/naf-10",
  "https://naf.com.sa/projects/naf-8",
  "https://ajwd-sa.com/project/أجود-42",
  "https://naf.com.sa/projects/naf-9",
  "https://www.rasf.sa/listing/dh-yrd-19",
  "https://www.krsal.sa/projects/300964",
  "https://naf.com.sa/projects/naf-7",
  "https://naf.com.sa/projects/naf-6",
  "https://naf.com.sa/projects/naf-11",
  "https://naf.com.sa/projects/naf-12",
  "https://www.krsal.sa/projects/300962",
  "https://naf.com.sa/projects/naf-4",
  "https://naf.com.sa/projects/naf-5",
  "https://naf.com.sa/projects/naf-2",
  "https://senanrealestate.sa/projects/apartments-abha.html",
  "https://senanrealestate.sa/projects/apartments-siyari.html",
  "https://senanrealestate.sa/projects/apartments-shifa.html",
  "https://senanrealestate.sa/projects/apartments-rufaidah.html",
  "https://senanrealestate.sa/projects/upper-rufaidah.html",
  "https://naf.com.sa/projects/naf-3",
  "https://naf.com.sa/projects/naf-13",
  "https://naf.com.sa/projects/naf-1",
  "https://retal.com.sa/en/properties/ewan-sedra-4/",
  "https://retal.com.sa/en/properties/nesaj-al-fursan-2/",
  "https://retal.com.sa/en/properties/rbc-qurtuba/",
  "https://retal.com.sa/en/properties/ewan-sedra-2/",
  "https://retal.com.sa/en/properties/ewan-sedra-3/",
  "https://retal.com.sa/en/properties/the-ritz-carlton-khobar/",
  "https://retal.com.sa/en/properties/ewan-sedra/",
  "https://sumou.com.sa/eng/homepage-en/",
  "https://www.krsal.sa/projects/300963",
  "https://rasf.sa/listing/le-anglo",
  "https://rasf.sa/listing/hrbr-bwn",
  "https://rasf.sa/listing/aarq-lyt-24",
  "https://rasf.sa/listing/inspire",
  "https://alhazem.com.sa/state/متاح/",
  "https://alhazem.com.sa/project/2-فلل-البساتين/",
  "https://darco.com.sa/news/6c447c1c-d73a-4003-926d-84ab4b021f33",
  "https://retal.com.sa/en/properties/deera/",
  "https://retal.com.sa/en/properties/terra-riyadh/",
  "https://www.rasf.sa/listing/aarq-lyt-23",
  "https://www.rasf.sa/listing/mndfyl-20",
  "https://www.rasf.sa/listing/aarq-2",
  "https://www.rasf.sa/listing/aarq-11",
  "https://www.rasf.sa/listing/mndfyl-9",
  "https://www.rasf.sa/listing/aarq-18",
  "https://www.rasf.sa/listing/araqa-1",
  "https://www.rasf.sa/listing/dem-7",
  "https://www.rasf.sa/listing/araqah-4",
  "https://aswar.com.sa/our-projects/marquise",
  "https://aswar.com.sa/our-projects/aswar-qortoba",
  "https://shahm.re/projects/scarlet",
  "https://shahm.re/projects/emerald",
  "https://shahm.re/projects/sapphire",
  "https://shahm.re/projects/veloria",
  "https://shahm.re/projects/variant",
  "https://shahm.re/projects/shahm-one",
  "https://senanrealestate.sa/projects/villas-al-mahala.html",
  "https://senanrealestate.sa/projects/ghaim-house.html",
  "https://senanrealestate.sa/projects/upper-rooms-raqi.html",
  "https://www.razre.sa/projects/raz-elevate/"
]
UA = "SAE-DB-public-firstparty-unit-research/1.0"
OUT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "sae_original_87_pages_source_only.json"
CODE = re.compile(r"(?:[A-Z]{1,9}[-_]?\d{1,5}[A-Z]?(?:[-_][A-Z0-9]{1,6})?|[A-Z][-][A-Z0-9]{1,8}|[A-Z][0-9]{1,5}[-][A-Z0-9]{1,6}|[0-9]{1,4}[-][A-Z0-9]{1,5})", re.I)
COLUMN_HINT = ("الوحدة", "رقم الوحدة", "رقم الشقة", "رقم الفيلا", "شقة", "محل", "القطعة", "unit", "apartment", "villa", "property", "shop")
state = {"schema":"SAE_PUBLIC_87_EXACT_FIRSTPARTY_URL_UNIT_TABLE_DISCOVERY_V1",
         "started_at_utc":datetime.now(timezone.utc).isoformat(),"state":"STARTED",
         "planned_public_urls":len(URLS),"pages":[],"firstparty_itemized_candidate_rows":[],
         "robots_checks":[],"errors":[],"private_canonical_ids":False,"canonical_writes":0}
robots_cache = {}
def save():
    OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def text(el):
    return " ".join(" ".join(el.itertext()).split())[:500]
def fetch(url, host):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != host or parsed.username or parsed.password:
        raise ValueError("Source hostname changed")
    r = Fetcher.get(url,retries=0,timeout=35,follow_redirects="safe",
                    headers={"User-Agent":UA})
    if int(r.status)==429:
        raise RuntimeError("HTTP_429_GLOBAL_STOP")
    target=urlsplit(str(r.url))
    if target.scheme!="https" or target.hostname!=host:
        raise ValueError("Off-source redirect")
    return r
def robots(host):
    if host in robots_cache:return robots_cache[host]
    robot_url="https://"+host+"/robots.txt"
    try:
        res=fetch(robot_url,host)
        if int(res.status)!=200:
            state["robots_checks"].append({"host":host,"status":int(res.status),"policy":"HOST_SKIPPED"})
            robots_cache[host]=None;return None
        p=RobotFileParser()
        p.parse(res.body.decode("utf-8","replace").splitlines())
        robots_cache[host]=p
        state["robots_checks"].append({"host":host,"status":200,"policy":"EXPLICIT_PARSE"})
        return p
    except RuntimeError:
        raise
    except Exception as e:
        state["robots_checks"].append({"host":host,"status":"NETWORK_FAIL","error":str(e)[:120]})
        robots_cache[host]=None;return None
def candidates(raw, url):
    root=LX.fromstring(raw)
    title=text(root.xpath("//h1[1]")[0]) if root.xpath("//h1[1]") else ""
    result=[];seen=set();tables=root.xpath("//table")
    for ti,table in enumerate(tables):
        trs=table.xpath(".//tr")
        heading=" ".join(text(el) for el in table.xpath(".//thead//th")[:12])
        if not heading and trs:
            heading=" ".join(text(el) for el in trs[0].xpath("./th")[:12])
        if not any(q in heading.lower() for q in COLUMN_HINT):
            continue
        for tr in trs[:500]:
            columns=[text(c) for c in tr.xpath("./td")[:12]]
            if len(columns)<3:
                continue
            label=columns[0]
            if not label or len(label)>90:
                continue
            has_code=CODE.fullmatch(label.strip()) is not None
            if not has_code:
                continue  # do not fabricate physical identities from aggregate/model rows
            key=label.strip().upper()
            if key in seen:continue
            seen.add(key)
            # Store only public unit-table cells; strip emails or long contacts.
            clean=[re.sub(r"\b\S+@\S+\b", "[email redacted]",z)[:160] for z in columns]
            result.append({"source_url":url,"table_no":ti,"table_header":heading[:250],
                           "original_first_column_identifier":label,"original_public_unit_row_cells":clean,
                           "review_state":"SOURCE_ONLY_CANDIDATE_NOT_CANONICAL_UNIT"})
    return {"publisher_h1":title,"html_tables":len(tables),"candidate_rows":result}
try:
    seen_urls=set()
    for index,url in enumerate(URLS):
        if url in seen_urls:continue
        seen_urls.add(url)
        host=urlsplit(url).hostname
        if not host:
            continue
        p=robots(host)
        entry={"public_original_url":url,"host":host,"order":index+1}
        if p is None:
            entry["state"]="SKIP_ROBOTS_NOT_AVAILABLE";state["pages"].append(entry);save();continue
        if not p.can_fetch(UA,url):
            entry["state"]="SKIP_ROBOTS_DISALLOW";state["pages"].append(entry);save();continue
        time.sleep(max(2.0,float(p.crawl_delay(UA) or p.crawl_delay("*") or 0)))
        try:
            res=fetch(url,host)
            entry["http_status"]=int(res.status)
            if int(res.status)!=200:
                entry["state"]="SKIP_NON_200"
            else:
                body=res.body
                if not isinstance(body,bytes) or len(body)>3_000_000 or not body:
                    entry["state"]="SKIP_BAD_RESPONSE_SIZE"
                else:
                    extracted=candidates(body.decode("utf-8","replace"),str(res.url))
                    entry["publisher_h1"]=extracted["publisher_h1"]
                    entry["html_tables"]=extracted["html_tables"]
                    entry["source_itemized_candidate_rows"]=len(extracted["candidate_rows"])
                    entry["state"]="SOURCE_ONLY_CAPTURED"
                    state["firstparty_itemized_candidate_rows"].extend(extracted["candidate_rows"])
        except RuntimeError as e:
            if "HTTP_429_GLOBAL_STOP" in str(e):
                entry["state"]="STOPPED_HTTP_429";state["pages"].append(entry);save();raise
            entry["state"]="SOURCE_ERROR";entry["error"]=str(e)[:160]
        except Exception as e:
            entry["state"]="SOURCE_ERROR";entry["error"]=type(e).__name__+": "+str(e)[:150]
        state["pages"].append(entry)
        save()
        print("SOURCE_PROBE",json.dumps({"i":index+1,"host":host,"status":entry["state"],
              "coded_rows":entry.get("source_itemized_candidate_rows",0)},ensure_ascii=False),flush=True)
    state["state"]="COMPLETE_SOURCE_ONLY"
except RuntimeError as e:
    state["state"]="STOPPED_HTTP_429" if "HTTP_429_GLOBAL_STOP" in str(e) else "STOPPED_RUNTIME_ERROR"
    state["errors"].append(str(e)[:200])
finally:
    state["finished_at_utc"]=datetime.now(timezone.utc).isoformat()
    state["total_candidate_source_rows"]=len(state["firstparty_itemized_candidate_rows"])
    save()
    print("RESULT",json.dumps({"status":state["state"],"source_urls_scanned":len(state["pages"]),
         "candidate_source_rows":state["total_candidate_source_rows"],"blocked_hosts":[x["host"] for x in state["robots_checks"] if x.get("policy")=="HOST_SKIPPED"],
         "master_writes":0},ensure_ascii=False),flush=True)
if state["state"] not in ("COMPLETE_SOURCE_ONLY",):
    raise SystemExit(2)
