#!/usr/bin/env python3
"""Deterministic fixture used only to self-test the EREI eval harness."""

import json
import sys

request = json.load(sys.stdin)

response = {
    "output": "Affected layers: frontend, backend. Risk L2.",
    "metadata": {
        "risk": "L2",
        "echo_case_id": request.get("case_id"),
    },
    "trace": [
        {"type": "tool", "name": "impact-analysis"}
    ],
}

print(json.dumps(response))
