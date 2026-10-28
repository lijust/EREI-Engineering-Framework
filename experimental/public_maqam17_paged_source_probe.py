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
                if n==1:
                    state["paging_diagnostic"]={"buttons":(await page.locator("button").all_inner_texts())[:50],
                      "number_text_counts":{str(i):await page.get_by_text(str(i),exact=True).count() for i in range(2,8)},
                      "pagination_markup":(await page.locator("table").first.evaluate("e=>e.parentElement.parentElement.outerHTML.slice(-8500)")) if await page.locator("table").count() else ""}
                    out.write_text(json.dumps(state,ensure_ascii=False,indent=2))
                if n==7:break
                buttons=page.locator("button")
                selected=None
                for b in range(await buttons.count()):
                    element=buttons.nth(b)
                    if (await element.inner_text()).strip()==str(n+1):
                        selected=element
                        break
                if selected is None:break
                await selected.click(timeout=10000)
            await browser.close()
        state["status"]="COMPLETE"
    except Exception as e:state.update(status="FAILED",error=str(e))
    finally:
        out.write_text(json.dumps(state,ensure_ascii=False,indent=2))
        print(json.dumps({"status":state["status"],"pages":len(state["pages"]),"rows":sum(len(x["rows"]) for x in state["pages"])},ensure_ascii=False))
    if state["status"]!="COMPLETE":raise SystemExit(1)

asyncio.run(main())
