#!/usr/bin/env python3
"""SAE site-intelligence pilot: original public publisher units-source mapping.

Read-only recon, never writes SAE production. Public, robots-gated developer pages.
No authentication, proxy rotation, CAPTCHA bypass, or form submission.
Strict HTTP 429 global stop. Historical marketing totals != individual unit codes.
"""
from __future__ import annotations
import json, os, re, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from scrapling.fetchers import Fetcher, DynamicFetcher

UA = "SAE-Site-Intelligence-Research/1.0"
SITES = [
    {"key": "rafal-marvela", "url": "https://www.rafal.com.sa/communities/marvela",
     "name": "Marvela", "published_aggregate": 594},
    {"key": "kooheji-vellano", "url": "https://koohejidevelopment.sa/community/vellano/",
     "name": "Vellano", "published_aggregate": 1250},
    {"key": "darco-public-units", "url": "https://darco.com.sa/units",
     "name": "Darco units", "published_aggregate": None},
]
OUT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "sae_site_intelligence_firstparty_three_sites.json"
state = {"schema": "SAE_SITE_INTELLIGENCE_V1_FIRSTPARTY_BROWSER_NETWORK_RECON",
         "utc": datetime.now(timezone.utc).isoformat(),
         "scope": "PUBLIC_READ_ONLY_SOURCE_RECON", "sites": [], "status": "STARTED",
         "master_writes": 0, "research_writes": 0, "errors": []}
def save():
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=2)+"\n", encoding="utf8")

def cleaned(url):
    u = urlsplit(str(url))
    if u.scheme not in ("http", "https"):
        return ""
    return urlunsplit((u.scheme, u.netloc, u.path, "", ""))[:300]

def get(url):
    r = Fetcher.get(url, retries=0, timeout=30, follow_redirects="safe",
                    headers={"User-Agent": UA})
    if int(r.status) == 429:
        raise RuntimeError("GLOBAL_STOP_429")
    return r

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []; self.scripts = []; self._a = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self._a = {"href": attrs.get("href", ""), "text": []}
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
    def handle_data(self, data):
        if self._a is not None and data.strip():
            self._a["text"].append(data.strip())
    def handle_endtag(self, tag):
        if tag == "a" and self._a is not None:
            self.links.append({"href": self._a["href"], "text": " ".join(self._a["text"])[:130]})
            self._a = None

def source_robots(site):
    u = urlsplit(site["url"])
    robots_url = u.scheme + "://" + u.netloc + "/robots.txt"
    rr = get(robots_url)
    rp = RobotFileParser()
    if int(rr.status) == 200:
        rp.parse(rr.body.decode("utf8", "replace").splitlines())
    elif int(rr.status) == 404:
        rp.parse([])
    else:
        raise RuntimeError("ROBOTS_UNAVAILABLE_"+str(rr.status)+"_"+site["key"])
    if not rp.can_fetch(UA, site["url"]):
        raise RuntimeError("ROBOTS_DISALLOW_"+site["key"])
    return max(3.0, float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))

def classify_json(data):
    """Return non-sensitive shapes only. Never export entire API response."""
    found = []
    keys = ("unitNumber", "unit_number", "unitCode", "unit_code",
            "propertyId", "property_id", "projectId", "project_id",
            "area", "price", "bedrooms", "bathrooms", "totalUnits",
            "unitType", "status", "number")
    def walk(obj, path="$", depth=0):
        if depth>4 or len(found)>45:
            return
        if isinstance(obj, list):
            found.append({"path": path, "array_length": len(obj),
                          "first_item_fields": list(obj[0])[:32] if obj and isinstance(obj[0], dict) else []})
            if obj:
                walk(obj[0], path+"[0]", depth+1)
        elif isinstance(obj, dict):
            if any(k in obj for k in keys):
                found.append({"path": path, "visible_field_names": [k for k in keys if k in obj]})
            for k,v in list(obj.items())[:26]:
                if isinstance(v, (list,dict)):
                    walk(v, path+"."+str(k)[:40], depth+1)
    walk(data)
    return found[:45]

def get_browser(site, record):
    """DynamicFetcher uses standard Playwright. No stealth or bypass."""
    action_data = {}
    def inspect(page):
        action_data["url_after_load"] = cleaned(page.url)
        action_data["buttons"] = [x.strip()[:100] for x in page.locator("button").all_inner_texts() if x.strip()][:35]
        action_data["select_count"] = page.locator("select").count()
        action_data["table_rows"] = page.locator("table tbody tr").count()
        action_data["data_unit_nodes"] = page.locator("[data-unit-id], [data-unit-number], [data-unit-code]").count()
        action_data["unit_links"] = []
        for a in page.locator("a[href]").all():
            h = a.get_attribute("href") or ""
            if re.search(r"(unit|apartment|property|villa|available|availability|inventory)", h, re.I):
                action_data["unit_links"].append({"url": cleaned(urljoin(page.url, h)), "text": a.inner_text()[:90]})
                if len(action_data["unit_links"]) >= 45:
                    break
        body = " ".join(page.locator("body").inner_text(timeout=10000).split())
        action_data["visible_text_head"] = body[:1700]
        # Read-only click ONLY if a clear availability control, not nested in a form.
        if site["key"]=="rafal-marvela":
            btn = page.get_by_role("button", name=re.compile(r"View Units Availability",re.I))
            if btn.count()==1 and btn.locator("xpath=ancestor::form").count()==0:
                btn.click(timeout=9000)
                page.wait_for_timeout(2200)
                action_data["availability_button_clicked"] = True
                action_data["url_after_availability"] = cleaned(page.url)
                action_data["after_click_tables"] = page.locator("table tbody tr").count()
                action_data["after_click_text_head"] = " ".join(page.locator("body").inner_text(timeout=10000).split())[:1800]
    response = DynamicFetcher.fetch(site["url"], retries=0, timeout=50000,
                                    capture_xhr=r".+", page_action=inspect,
                                    network_idle=False, headless=True, disable_resources=True)
    if int(response.status)==429:
        raise RuntimeError("GLOBAL_STOP_429")
    record["browser"] = {"http": int(response.status), "details": action_data, "xhr": []}
    for x in getattr(response, "captured_xhr", []):
        if int(x.status)==429:
            raise RuntimeError("GLOBAL_STOP_429")
        url = urlsplit(str(x.url))
        if url.scheme not in ("http", "https"):
            continue
        if int(x.status)!=200:
            record["browser"]["xhr"].append({"url":cleaned(x.url), "http":int(x.status)})
            continue
        raw = x.body
        if not isinstance(raw, bytes) or not 0<len(raw)<3_000_000:
            continue
        try:
            item = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            continue
        shape = classify_json(item)
        if shape:
            record["browser"]["xhr"].append({"url":cleaned(x.url), "http":200,
                 "firstparty":url.hostname in ("www.rafal.com.sa","rafal.com.sa","koohejidevelopment.sa","darco.com.sa"),
                 "shape":shape[:12]})
    record["browser"]["xhr"] = record["browser"]["xhr"][:120]
    record["browser"]["xhr_matching_item_fields_count"] = len(
        [x for x in record["browser"]["xhr"] if x.get("shape")])

try:
    for site in SITES:
        rec = {"key":site["key"], "url":site["url"],"name":site["name"],
               "published_aggregate_not_individual":site["published_aggregate"],
               "unit_cards_confirmed":0,"stages":[]}
        state["sites"].append(rec)
        delay = source_robots(site)
        time.sleep(delay)
        resp = get(site["url"])
        if int(resp.status)!=200:
            rec["status"]="HTTP_"+str(resp.status)
            save()
            continue
        final = urlsplit(str(resp.url))
        initial = urlsplit(site["url"])
        if final.hostname!=initial.hostname:
            raise ValueError("UNEXPECTED_SOURCE_REDIRECT_"+site["key"])
        html = resp.body.decode("utf8", "replace")
        links = Links(); links.feed(html)
        interesting = []
        for a in links.links:
            u = urljoin(site["url"],a["href"])
            if re.search(r"\.(?:pdf)(?:$|\?)|/(?:units?|properties|apartments?|inventory|villas?)(?:/|$)|availability",u,re.I):
                interesting.append({"url": cleaned(u), "text": a["text"]})
        rec["static"]={"http":int(resp.status),"bytes":len(resp.body),
            "scripts":len(links.scripts),"next_data":'id="__NEXT_DATA__"' in html,
            "public_links":interesting[:50],
            "number_of_listing_links":len(interesting),
            "html_unit_label_occurrences":len(re.findall(r"unit number|unit code|رقم الوحدة",html,re.I))}
        rec["stages"].append("static")
        save()
        time.sleep(delay)
        try:
            get_browser(site, rec)
            rec["stages"].append("browser_xhr")
        except Exception as e:
            if "GLOBAL_STOP_429" in str(e):
                raise
            rec["browser_error"]=type(e).__name__+": "+str(e)[:230]
        rec["status"]="DIAGNOSTIC_COMPLETE"
        save()
        print("SITE_INTEL "+json.dumps({"site":site["key"],
         "links":len(interesting),"xhr_shapes":rec.get("browser",{}).get("xhr_matching_item_fields_count"),
         "browser_error":rec.get("browser_error")},ensure_ascii=False),flush=True)
    state["status"]="COMPLETE_SOURCE_INTELLIGENCE_ONLY"
except Exception as exc:
    state["status"]="STOP_HTTP429" if "GLOBAL_STOP_429" in str(exc) else "STOP_SOURCE_ERROR"
    state["errors"].append(type(exc).__name__+": "+str(exc)[:320])
finally:
    save()
    print("SITE_INTELLIGENCE_FINAL "+json.dumps({"status":state["status"],
      "tested":len(state["sites"]),"errors":state["errors"]},ensure_ascii=False),flush=True)
if state["status"]!="COMPLETE_SOURCE_INTELLIGENCE_ONLY":
    raise SystemExit(2)
