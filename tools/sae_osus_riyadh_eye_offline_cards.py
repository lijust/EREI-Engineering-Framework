#!/usr/bin/env python3
"""Print first-party original OSUS Eye card sections from saved public capture, no writes."""
import json,re
from pathlib import Path
o=json.loads(Path("sae-osus-riyadh-original-unit-inventory.json").read_text())
print("OSUS_EYE_HTML",json.dumps({"http":o.get("http"),"candidate":o.get("canonical_project_candidate"),"final_body":o.get("final_body"),"links":o.get("final_links"),"initial":o.get("initial")},ensure_ascii=False),flush=True)
for r in o.get("responses",[]):
 print("OSUS_EYE_API",json.dumps({"url":r["url"],"bytes":r["bytes"],"mime":r.get("content_type"),"original_excerpt":r.get("original_response_excerpt","")[:1500]},ensure_ascii=False),flush=True)
codes=o.get("visible_oe_codes",[])
assert len(codes)==9 and len(set(codes))==9
print("OSUS_EYE_QUALIFIED_SOURCE_CODES",json.dumps(codes,ensure_ascii=False),flush=True)
