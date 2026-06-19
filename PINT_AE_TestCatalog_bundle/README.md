# PINT-AE Scenario Catalog — `third_round` (authoritative deliverable)

**Start here.** This folder is the authoritative UAE PINT-AE e-invoice **scenario catalog**: the
complete document-content space of e-invoice scenarios, each flagged VALID/INVALID and machine-verified
against the **real compiled PINT-AE schematron**. **FROZEN as the certified `v2.0` final catalog**
(`FROZEN.md`, git tag `v2.0`) — do not edit/regenerate; the channel exercise (`fourth_round`) consumes it.
`../second_round/` is the superseded `v1.0` snapshot.

## What this is (and is not)
- **Is:** the **channel-independent** e-invoice document space — every scenario the schematron can
  validate, with a complete one-negative-per-fatal-assert bijection, the full doctype × tax-category
  positive matrix, an exhaustively classified flag space, and a vendor-grade defect register.
- **Is not:** ingestion-channel coverage (Form/XML/JSON/Bulk-Excel/API), serializer/backend layer,
  or TDD/C5 reporting. Those are a **separate, downstream exercise** that consumes this catalog by
  its stable `TestCaseID`s (see [`ID_SCHEME.md`](./ID_SCHEME.md)).

## Live numbers (verify with the snippet below)
- **746 rows** = **351 Positive + 358 Negative + 37 Domain-note**.
- **738 `VERIFIED` + 8 `DOCUMENTED`** (`Status` column).
- **738 / 738 machine-verified, 0 mismatch** against the schematron (`schematron_validation.csv`).
- **302 / 302 fatal-assert negative bijection** (294 executable + 8 documented).
- **100 %** `SourceRef` coverage; every negative has an `ExpectedRuleID`.

> The **8 `DOCUMENTED` rows are NOT machine-verified** — they are real fatal asserts that are
> genuinely unreachable through the harness (dead / compiler-dead / XSLT-runtime-crash /
> predicate-shadowed), kept for bijection completeness with a typed reason. See
> [`DEFECT_REGISTER.md`](./DEFECT_REGISTER.md) §B. This demarcation is deliberate — keep it crisp.

```bash
python3 -c "import csv;from collections import Counter;r=list(csv.DictReader(open('third_round/PINT_AE_TestCatalog.csv')));print(len(r),Counter(x['Status'] for x in r),Counter(x['Kind'] for x in r))"
```

## File map — read in this order

| File | What it is |
|------|-----------|
| **`README.md`** (this file) | Index + start-here. |
| **[`COMPLETENESS_CERTIFICATE.md`](./COMPLETENESS_CERTIFICATE.md)** | The four proven completeness claims + explicit scope/exclusions + reproduce block. The client-facing attestation. |
| **[`DATA_DICTIONARY.md`](./DATA_DICTIONARY.md)** | Every one of the 25 CSV columns: meaning, enum, derived-vs-authored, machine-verified-or-not. Read before consuming the CSV. |
| **[`ID_SCHEME.md`](./ID_SCHEME.md)** | `TestCaseID` taxonomy + the stability/uniqueness contract for the downstream channel exercise. |
| **[`DEFECT_REGISTER.md`](./DEFECT_REGISTER.md)** | 14 vendor-grade findings (`.gc`↔`.sch` divergences, schematron defects/unreachable rules, non-obvious constraints) + the 8 documented rows (§B). |
| **[`RECONCILE_REPORT.md`](./RECONCILE_REPORT.md)** | Predicted-vs-actual reconciliation narrative. |
| `PINT_AE_TestCatalog.csv` / `.xlsx` | **The catalog** (746 rows × 25 cols). Generated — do not hand-edit. |
| `PINT_AE_TestCatalog_bundle.zip` | Self-contained client bundle (catalog + docs + instances + matrices). |
| `catalog_xml/` | The built instance XML per row (what the schematron actually validated). |
| `flag_combo_matrix.tsv` + `flag_combo_findings.md` | The exhaustive 1,536-cell flag-space classification. |
| `schematron_validation.csv` | The 738/738 machine-verification result (`result` = `MATCH`). |
| Pipeline: `assemble.py` → `build_bundle.py`; verifiers `verify_instances.py`, `validate_against_schematron.py`; `pilot/` runners | Regenerate + verify everything. |

> Canonical specs are shared in [`../.claude/rules/`](../.claude/rules/) (`positives-catalog.md`,
> `schema-assert-inventory.tsv`, `schema-validity-oracle.md`, `validator-harness.md`, …) — round-agnostic.

## Reproduce (from the repo root)
```bash
python3 third_round/assemble.py                       # regenerate catalog from specs (GUARD must pass)
python3 third_round/build_bundle.py                   # regenerate CSV/xlsx/zip + catalog_xml instances
python3 third_round/verify_instances.py               # instance ↔ metadata   → ✓ ALL match
python3 third_round/validate_against_schematron.py    # instance ↔ schematron  → 738/738 MATCH
```
Engine: Saxon-HE 12.9 + xmlresolver 5.3.3 on the Java classpath — setup in
[`../.claude/rules/validator-harness.md`](../.claude/rules/validator-harness.md). Headless,
deterministic, no network.

## To iterate (pre-freeze)
1. Add/adjust specs (in `../.claude/rules/` for positives/asserts, or the round TSVs here).
2. Build instances via the relevant `pilot/` runner.
3. `python3 third_round/assemble.py && python3 third_round/build_bundle.py`.
4. `python3 third_round/verify_instances.py && python3 third_round/validate_against_schematron.py`.
5. Commit. At a milestone, the maintainer freezes the round and spins the next.
