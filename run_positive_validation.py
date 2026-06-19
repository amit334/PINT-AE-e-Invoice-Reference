#!/usr/bin/env python3
"""
Batch-validate all positive scenario XMLs.
Prints a pass/fail table, then a detailed breakdown of every failure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate import validate

POS_DIR = Path(__file__).parent / "positive-xml-scenarios"

files = sorted(POS_DIR.glob("pos-*.xml"))
if not files:
    print(f"No files found in {POS_DIR}")
    sys.exit(1)

passed, failed = [], []

print(f"\nValidating {len(files)} positive-scenario XMLs ...\n")
print(f"{'#':<5} {'File':<55} {'Status':<10} Fatals  Warnings")
print("-" * 100)

for i, f in enumerate(files, 1):
    try:
        r = validate(f)
    except Exception as e:
        print(f"{i:<5} {f.name:<55} {'ERROR':<10} {e}")
        failed.append((f.name, None, str(e)))
        continue

    fatals   = r.fatal_count
    warnings = r.warning_count
    status   = "PASS" if r.is_valid else "FAIL"
    warn_str = f"{warnings} warn" if warnings else "-"
    print(f"{i:<5} {f.name:<55} {status:<10} {fatals:<7} {warn_str}")

    if r.is_valid:
        passed.append(f.name)
    else:
        failed.append((f.name, r, None))

# ── Summary ──────────────────────────────────────────────────────────────────
print("-" * 100)
print(f"\nResult: {len(passed)} PASSED  |  {len(failed)} FAILED  (out of {len(files)})\n")

if not failed:
    print("All positive scenarios passed validation.")
    sys.exit(0)

# ── Detail failures ──────────────────────────────────────────────────────────
print("=" * 100)
print("FAILURE DETAILS")
print("=" * 100)

for fname, result, exc in failed:
    print(f"\n{'─'*80}")
    print(f"FILE: {fname}")
    if exc:
        print(f"  EXCEPTION: {exc}")
        continue
    for issue in result.issues:
        if issue.flag == "fatal":
            print(f"  [FATAL]   {issue.rule_id}")
            print(f"            {issue.message}")
            print(f"            @ {issue.location}")
    warnings = [i for i in result.issues if i.flag == "warning"]
    if warnings:
        print(f"  ({len(warnings)} warnings suppressed)")

print()
sys.exit(1)
