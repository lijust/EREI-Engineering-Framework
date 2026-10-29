#!/usr/bin/env python3
"""Menaco Rise PRJ-000132: official public apartment inventory UI deep probe.

Read-only. No inferring its 49 marketing total as original physical units.
"""
import asyncio,json,re,urllib.request,urllib.robotparser,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
from playwright.async_api import async_playwright
PAGE="https://menaco.sa/listings/178544"
PID="PRJ-000132"
UA="SAE-DB-Menaco-Rise-original-source-study/1.0"
OUT=Path("sae-mena-rise-native-original-unit-cards.json")
RE_CODE=re.compile(r"^\d+\s*[–-]\s*\d+\s*[bB][rR]$")
def robots_ok():
 rp=urllib.robotparser.RobotFileParser()
 with urllib.request.urlopen(urllib.request.Request("https://menaco.sa/robots.txt",headers={"User-Agent":UA}),timeout=15) as r:
  if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
  rp.parse(r.read(150000).decode("utf8","replace").splitlines())
 return rp.can_fetch(UA,PAGE)
async def main():
 output={"schema":"SAE_EXISTING_PRJ_000132_MENACO_RISE_NATIVE_ITEMIZED_UI_V1","original_url":PAGE,"canonical_project_id":PID,"source_id":"SRC-000204","timestamp_utc":datetime.now(timezone.utc).isoformat(),"production_writes":0,"stages":[],"xhr":[],"errors":[]}
 try:ok=await asyncio.to_thread(robots_ok)
 except Exception as e:output["state"]="ROBOTS_UNVERIFIED_"+type(e).__name__;OUT.write_text(json.dumps(output));return
 if not ok:output["state"]="ROBOTS_DISALLOWED";OUT.write_text(json.dumps(output));return
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True)
  page=await b.new_page(user_agent=UA,viewport={"width":1400,"height":1000})
  tasks=[];blocked=False
  async def record(r):
   nonlocal blocked
   if urlsplit(r.url).hostname not in ("menaco.sa","www.menaco.sa"):return
   if r.status in (403,429):blocked=True;output["errors"].append("SOURCE_HTTP_"+str(r.status));return
   if r.status!=200 or r.request.resource_type not in ("fetch","xhr"):return
   try:
    raw=await r.body()
    if len(raw)>4000000:return
    if len(output["xhr"])<30:output["xhr"].append({"path":urlsplit(r.url).path,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"excerpt":raw[:350].decode("utf8","replace")})
   except Exception as e:output["errors"].append("XHR_"+type(e).__name__)
  page.on("response",lambda r:tasks.append(asyncio.create_task(record(r))))
  try:
   r=await page.goto(PAGE,wait_until="domcontentloaded",timeout=45000)
   output["http"]=r.status if r else None
   if output["http"]==200:
    await page.wait_for_timeout(1500)
    for label in ("عرض الشقق","عرض الوحدات"):
     l=page.get_by_text(label,exact=True)
     if await l.count() and await l.first.is_visible():
      await l.first.click(timeout=3500)
      output["clicked"]=label
      await page.wait_for_timeout(2500)
      break
    old=""
    for step in range(13):
     if blocked:break
     body=(await page.locator("body").inner_text())[:150000]
     cards=[t.strip() for t in body.splitlines() if RE_CODE.fullmatch(t.strip())]
     output["stages"].append({"step":step,"exact_source_code_lines":cards,"body_text":body,"load_more_html":await page.locator('button[wire\\:click="loadMore"]').evaluate_all("(a)=>a.map(x=>x.outerHTML.slice(0,500))")})
     fingerprint=hashlib.sha256(body.encode()).hexdigest()
     if fingerprint==old:break
     old=fingerprint
     load=page.locator('button[wire\\:click="loadMore"]')
     if not await load.count() or not await load.first.is_visible() or not await load.first.is_enabled():break
     await load.first.click(timeout=4500)
     try:
      await page.wait_for_function("""(n)=> {
       let t=document.body.innerText||'';
       let codes=t.match(/^\\d+\\s*[–-]\\s*\\d+\\s*[bB][rR]$/gm)||[];
       return codes.length>n;
      }""",arg=len(cards),timeout=12000)
     except Exception:output["errors"].append("NO_ADDITIONAL_ORIGINAL_CODE_AFTER_CLICK");break
  except Exception as e:output["errors"].append("PAGE_"+type(e).__name__+":"+str(e)[:160])
  if tasks:await asyncio.gather(*tasks,return_exceptions=True)
  output["blocked"]=blocked
  output["state"]="SOURCE_ONLY_CARDS" if output["stages"] and output["stages"][-1]["exact_source_code_lines"] else "NO_ITEMIZED_PUBLIC_UNITS"
  print("SAE_MENA_RISE_DEEP",json.dumps({"state":output["state"],"http":output.get("http"),"clicked":output.get("clicked"),"steps":len(output["stages"]),"last_codes":output["stages"][-1]["exact_source_code_lines"] if output["stages"] else [],"errors":output["errors"]},ensure_ascii=False)[:11000],flush=True)
  OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
  await page.close();await b.close()
if __name__=="__main__":asyncio.run(main())
