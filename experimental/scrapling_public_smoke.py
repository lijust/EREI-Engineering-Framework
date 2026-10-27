#!/usr/bin/env python3
"""Public, data-free Scrapling v0.5 GitHub-hosted runner smoke test.

No customer repository, developer/project identities, credentials, or
proprietary datasets are accessed. This is a test of the generic fetcher.
"""
from __future__ import annotations
import json
import platform
import sys
from datetime import datetime, timezone
from scrapling.fetchers import Fetcher

URL = "https://example.com/"
page = Fetcher.get(URL, retries=1, timeout=25, follow_redirects="safe")
body = page.body
assert isinstance(body, bytes) and b"Example Domain" in body, "Did not receive expected public example.com HTML"
assert int(page.status) == 200, f"Unexpected HTTP status: {page.status}"
print(json.dumps({
    "status": "PUBLIC_SCRAPLING_HTTP_FETCH_PASS",
    "python": sys.version.split()[0],
    "platform": platform.system(),
    "http_code": int(page.status),
    "body_bytes": len(body),
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "user_data_processed": False,
    "canonical_master_writes": 0,
}, sort_keys=True))
