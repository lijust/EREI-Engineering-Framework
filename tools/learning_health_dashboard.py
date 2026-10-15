#!/usr/bin/env python3
"""Render a compact deterministic Learning Health dashboard from analysis reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("report must be an object")
    return value


def render(pattern:dict,effectiveness:dict|None=None)->str:
    e=pattern.get("current_epoch",{})
    trigger=pattern.get("source",{}).get("state_trigger",{})
    lines=[
      "# EREI Learning Health",
      "",
      f"- Epoch: `{pattern.get('source',{}).get('state_epoch_id','unknown')}`",
      f"- Trigger: **{trigger.get('level','unknown')}**",
      f"- Material tasks: **{e.get('material_tasks',0)}**",
      f"- Rework-free task rate: **{e.get('rework_free_task_rate')}**",
      f"- Verification-clean task rate: **{e.get('verification_clean_task_rate')}**",
      f"- Verification-escape task rate: **{e.get('verification_escape_task_rate')}**",
      f"- Final failed-task rate: **{e.get('final_failed_task_rate')}**",
      f"- Rework cycles / material task: **{e.get('rework_cycles_per_material_task')}**",
      f"- Verification failures / material task: **{e.get('verification_failures_per_material_task')}**",
      "",
      "## Interpretation",
      "",
      "- Rework is iteration, not automatic task restart/failure.",
      "- Verification-failure rate is catch density, not final failure rate.",
      "- Verification escapes and final failed outcomes are stronger negative quality signals.",
      "",
      "## Pattern signals",
      ""
    ]
    signals=pattern.get("signals",[])
    if not signals: lines.append("- None above deterministic thresholds.")
    for s in signals:
        lines.append(f"- **{s.get('code','UNKNOWN')}** ({s.get('severity','unknown')}): {s.get('interpretation','')}")
    if effectiveness:
        lines += ["","## Before/after effectiveness","",
                  f"- Status: **{effectiveness.get('status','unknown')}**",
                  f"- Causation: **{effectiveness.get('causation','unknown')}**"]
        for k,v in effectiveness.get("primary_quality_signals",{}).items():
            lines.append(f"- {k}: **{v}**")
        reasons=effectiveness.get("comparability",{}).get("reasons",[])
        if reasons: lines.append("- Comparability cautions: "+", ".join(reasons))
    return "\n".join(lines)+"\n"


def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument("--pattern-report",required=True)
    p.add_argument("--effectiveness-report")
    p.add_argument("--output")
    args=p.parse_args(argv)
    try:
        pattern=_load(Path(args.pattern_report))
        effectiveness=_load(Path(args.effectiveness_report)) if args.effectiveness_report else None
        text=render(pattern,effectiveness)
        if args.output: Path(args.output).write_text(text,encoding="utf-8")
        else: print(text,end="")
        return 0
    except (OSError,json.JSONDecodeError,ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

if __name__=="__main__": raise SystemExit(main())
