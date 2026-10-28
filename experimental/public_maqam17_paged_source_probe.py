import asyncio, json, os
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright

URL="https://property.maqamco.sa/projects/301141"

async def main():
    out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"maqam17-pages.json"
    state={"source":URL,"date":datetime.now(timezone.utc).isoformat(),"pages":[],"status":"STARTED"}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            page=await browser.new_page(locale="ar-SA")
            resp=await page.goto(URL,wait_until="domcontentloaded",timeout=40000)
            if resp.status!=200:raise ValueError("HTTP_"+str(resp.status))
            for n in range(1,8):
                await page.wait_for_timeout(1800)
                fields=[]
                for row in await page.locator("table tbody tr").all():
                    cells=await row.locator("td").all_inner_texts()
                    fields.append(cells)
                state["pages"].append({"page":n,"rows":fields})
                out.write_text(json.dumps(state,ensure_ascii=False,indent=2))
                if n==7:break
                btn=page.get_by_role("button",name=str(n+1),exact=True)
                if not await btn.count():break
                await btn.first.click(timeout=10000)
            await browser.close()
        state["status"]="COMPLETE"
    except Exception as e:state.update(status="FAILED",error=str(e))
    finally:
        out.write_text(json.dumps(state,ensure_ascii=False,indent=2))
        print(json.dumps({"status":state["status"],"pages":len(state["pages"]),"rows":sum(len(x["rows"]) for x in state["pages"])},ensure_ascii=False))
    if state["status"]!="COMPLETE":raise SystemExit(1)

asyncio.run(main())
