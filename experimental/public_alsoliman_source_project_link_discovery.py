#!/usr/bin/env python3
"""Public Alsoliman exact selling project URLs read-only from developer portal."""
import json,os,re,time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from scrapling.fetchers import Fetcher

BASE="https://alsoliman.com.sa"
URL=BASE+"/ar/selling"
class Links(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.cur=None
    def handle_starttag(self,tag,attrs):
        if tag=="a": self.cur={"url":dict(attrs).get("href",""),"text":[]}
    def handle_data(self,s):
        if self.cur is not None:self.cur["text"].append(s.strip())
    def handle_endtag(self,tag):
        if tag=="a" and self.cur is not None:
            self.rows.append({"url":self.cur["url"],"label":" ".join(self.cur["text"]).strip()})
            self.cur=None
def main():
    dest=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"alsoliman-selling-source-projects.json"
    out={"source":URL,"status":"STARTED","links":[],"project_numbers":[],"canonical_writes":0}
    try:
        robots=Fetcher.get(BASE+"/robots.txt",retries=0,timeout=25)
        if int(robots.status)==429:raise RuntimeError("STOP429")
        from urllib.robotparser import RobotFileParser
        rp=RobotFileParser()
        if int(robots.status)==200:rp.parse(robots.body.decode("utf8","replace").splitlines())
        elif int(robots.status)==404:rp.parse([])
        else:raise RuntimeError("ROBOTS_"+str(robots.status))
        if not rp.can_fetch("*",URL):raise RuntimeError("ROBOTS_DISALLOW")
        time.sleep(2.5)
        page=Fetcher.get(URL,retries=0,timeout=25)
        if int(page.status)==429:raise RuntimeError("STOP429")
        if int(page.status)!=200:raise RuntimeError("HTTP_"+str(page.status))
        if urlsplit(str(page.url)).hostname!="alsoliman.com.sa":raise RuntimeError("OFFSITE")
        text=page.body.decode("utf8","replace")
        p=Links();p.feed(text)
        out["links"]=[{"url":urljoin(URL,x["url"]),"anchor":x["label"][:120]} for x in p.rows
                      if urlsplit(urljoin(URL,x["url"])).hostname=="alsoliman.com.sa"
                      and "selling/project/" in urljoin(URL,x["url"])]
        out["project_numbers"]=[{"number":n,"nearby_html":text[max(0,m.start()-200):m.end()+250]}
           for m in re.finditer(r"مشروع\s*(13[0-4])",text) for n in [m.group(1)]]
        out["status"]="COMPLETE"
    except Exception as e:out["status"]="ERROR";out["error"]=str(e)
    finally:
        dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps({"status":out["status"],"links":len(out["links"]),"project_numbers":len(out["project_numbers"]),"error":out.get("error")},ensure_ascii=False))
    if out["status"]!="COMPLETE":raise SystemExit(1)
if __name__=="__main__":main()
