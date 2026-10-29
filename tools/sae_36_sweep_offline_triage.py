#!/usr/bin/env python3
"""Offline triage of one 36-site sweep, retain real publisher URLs; no source requests."""
import json,re,collections
from pathlib import Path
d=json.loads(Path("sae-36-source-tiered-sweep.json").read_text())
print("SWEEP_SUMMARY",json.dumps(d.get("summary",{}),ensure_ascii=False),flush=True)
for r in d["results"]:
 ini=r.get("initial") or {};final=r.get("final") or {}
 links=final.get("links") or ini.get("links") or []
 html=r.get("public_excerpt","")
 scripts=final.get("scripts") or ini.get("scripts") or []
 iframes=final.get("iframes") or ini.get("iframes") or []
 xhr=r.get("xhr") or []
 buttons=final.get("buttons") or ini.get("buttons") or []
 candidate_anchors=[x for x in links if re.search("interactive|master|map|plan|المخطط|الخريطة|inventory|الوحدات|unit",x["url"]+" "+x.get("text",""),re.I)]
 print("SWEEP_DETAIL",json.dumps({"id":r["project_id"],"url":r["url"],"title":ini.get("title"),
 "access":r.get("access"),"status":r.get("status"),"xs":len(xhr),"xhr_urls":[x["path"] for x in xhr[:12]],
 "iframe_urls":iframes[:10],"links":candidate_anchors[:12],
 "script_urls":scripts[:8],
 "buttons":buttons[:22],
 "first_text":html[:550],"dom":ini.get("headings",0),"error":r.get("errors",[])[:2]},ensure_ascii=False),flush=True)
