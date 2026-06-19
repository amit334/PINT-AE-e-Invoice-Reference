#!/usr/bin/env python3
"""
Generate positive (valid) scenario XML files for PINT AE schematron validation.
Uses generate_xml.generate() so all outputs are schematron-compliant by construction.
  Seller endpoint : 1000454545
  Buyer endpoint  : 1000464646

Run:  python generate_positive_scenarios.py
Output: positive-xml-scenarios/  (68 files across 13 categories)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_xml import generate

OUT = Path(__file__).parent / "positive-xml-scenarios"
OUT.mkdir(exist_ok=True)

# Fixed party identifiers
SELLER_EP   = "1000454545"
BUYER_EP    = "1000464646"
SELLER_VAT  = "198765432102003"   # 15-digit UAE TRN (starts 1, ends 03)
BUYER_VAT   = "134567890123003"
SELLER_TL   = "112345678900003"   # Trade License
BUYER_TL    = "112345679000003"
SELLER_NAME = "Seller Legal Name LLC"
BUYER_NAME  = "Buyer Legal Name LLC"
FTZ_BENE    = "198765432100003"   # FTZ Beneficiary ID (BTAE-01)
AGENT_PRL   = "134567890120003"   # Agent Principal VAT ID (BTAE-14), must differ from SELLER_VAT

TXN_SHORT = {
    "Standard":   "std",
    "FTZ":        "ftz",
    "Deemed":     "deemed",
    "Margin":     "margin",
    "Summary":    "summary",
    "Continuous": "cont",
    "Agent":      "agent",
    "eCommerce":  "ecomm",
    "Exports":    "exports",
}
DOC_SHORT = {
    "380": "380-tax-inv",
    "381": "381-tax-cn",
    "389": "389-sb-inv",
    "261": "261-sb-cn",
    "480": "480-oos-inv",
    "81":  "081-oos-cn",
}

FILES = []

def gen(seq: int, doc: str, txn: str, vats: list, description: str):
    vat_part = "-".join(vats)
    fname = f"pos-{seq:03d}-{DOC_SHORT[doc]}-{TXN_SHORT[txn]}-vat-{vat_part}.xml"
    xml = generate(
        doc_type             = doc,
        vat_categories       = vats,
        transaction_type     = txn,
        supplier_endpoint_id = SELLER_EP,
        buyer_endpoint_id    = BUYER_EP,
        supplier_vat         = SELLER_VAT,
        buyer_vat            = BUYER_VAT,
        supplier_tl          = SELLER_TL,
        buyer_tl             = BUYER_TL,
        supplier_name        = SELLER_NAME,
        buyer_name           = BUYER_NAME,
        ftz_beneficiary_id   = FTZ_BENE,
        agent_principal_id   = AGENT_PRL,
    )
    (OUT / fname).write_text(xml, encoding="utf-8")
    FILES.append((fname, description))
    print(f"  OK  {fname}")


# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 1 — DOC 380 (Tax Invoice) × All 9 Transaction Types
# ─────────────────────────────────────────────────────────────────────────────
gen(1,  "380", "Standard",   ["S"],           "Tax Invoice / Standard / VAT S (5%)")
gen(2,  "380", "FTZ",        ["S"],           "Tax Invoice / Free Trade Zone / VAT S — BuyerCustomerParty/BeneficiaryID")
gen(3,  "380", "Deemed",     ["S"],           "Tax Invoice / Deemed Supply / VAT S — no DueDate/PaymentMeans")
gen(4,  "380", "Margin",     ["N"],           "Tax Invoice / Profit Margin Scheme / VAT N (5%) — no TaxPointDate")
gen(5,  "380", "Summary",    ["S"],           "Tax Invoice / Summary Invoice / VAT S — with InvoicePeriod")
gen(6,  "380", "Continuous", ["S"],           "Tax Invoice / Continuous Supply / VAT S — with InvoicePeriod")
gen(7,  "380", "Agent",      ["S"],           "Tax Invoice / Agent Sale / VAT S — SellerSupplierParty/PrincipalID")
gen(8,  "380", "eCommerce",  ["S"],           "Tax Invoice / E-Commerce / VAT S — with Delivery address")
gen(9,  "380", "Exports",    ["Z"],           "Tax Invoice / Exports / VAT Z — Delivery to non-AE country")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 2 — DOC 380 × All VAT Single Categories (Standard transaction)
# ─────────────────────────────────────────────────────────────────────────────
gen(10, "380", "Standard",   ["AE"],          "Tax Invoice / Standard / VAT AE (Reverse Charge) — Buyer VAT TRN mandatory")
gen(11, "380", "Standard",   ["Z"],           "Tax Invoice / Standard / VAT Z (Zero-Rated)")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 3 — DOC 381 (Tax Credit Note) × Key Transaction Types
# ─────────────────────────────────────────────────────────────────────────────
gen(12, "381", "Standard",   ["S"],           "Tax Credit Note / Standard / VAT S — BillingReference + DiscrepancyResponse")
gen(13, "381", "Standard",   ["AE"],          "Tax Credit Note / Standard / VAT AE")
gen(14, "381", "Standard",   ["Z"],           "Tax Credit Note / Standard / VAT Z")
gen(15, "381", "FTZ",        ["S"],           "Tax Credit Note / FTZ / VAT S")
gen(16, "381", "Deemed",     ["S"],           "Tax Credit Note / Deemed Supply / VAT S")
gen(17, "381", "Margin",     ["N"],           "Tax Credit Note / Profit Margin Scheme / VAT N")
gen(18, "381", "Summary",    ["S"],           "Tax Credit Note / Summary / VAT S — with InvoicePeriod")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 4 — DOC 389 (Self-Billing Invoice) × All VAT + Key Transaction Types
# ─────────────────────────────────────────────────────────────────────────────
gen(19, "389", "Standard",   ["S"],           "Self-Billing Invoice / Standard / VAT S")
gen(20, "389", "Standard",   ["AE"],          "Self-Billing Invoice / Standard / VAT AE — selfbilling CustomizationID")
gen(21, "389", "Standard",   ["Z"],           "Self-Billing Invoice / Standard / VAT Z")
gen(22, "389", "Standard",   ["E"],           "Self-Billing Invoice / Standard / VAT E (Exempt) — TaxExemptionReasonCode")
gen(23, "389", "Standard",   ["O"],           "Self-Billing Invoice / Standard / VAT O (Not Subject to VAT)")
gen(24, "389", "Margin",     ["N"],           "Self-Billing Invoice / Profit Margin Scheme / VAT N")
gen(25, "389", "FTZ",        ["S"],           "Self-Billing Invoice / FTZ / VAT S")
gen(26, "389", "Deemed",     ["S"],           "Self-Billing Invoice / Deemed Supply / VAT S")
gen(27, "389", "Summary",    ["S"],           "Self-Billing Invoice / Summary Invoice / VAT S")
gen(28, "389", "eCommerce",  ["S"],           "Self-Billing Invoice / E-Commerce / VAT S")
gen(29, "389", "Exports",    ["Z"],           "Self-Billing Invoice / Exports / VAT Z — non-AE delivery")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 5 — DOC 261 (Self-Billing Credit Note) × All VAT Categories
# ─────────────────────────────────────────────────────────────────────────────
gen(30, "261", "Standard",   ["S"],           "Self-Billing Credit Note / Standard / VAT S")
gen(31, "261", "Standard",   ["AE"],          "Self-Billing Credit Note / Standard / VAT AE")
gen(32, "261", "Standard",   ["Z"],           "Self-Billing Credit Note / Standard / VAT Z")
gen(33, "261", "Standard",   ["E"],           "Self-Billing Credit Note / Standard / VAT E")
gen(34, "261", "Standard",   ["O"],           "Self-Billing Credit Note / Standard / VAT O")
gen(35, "261", "Margin",     ["N"],           "Self-Billing Credit Note / Profit Margin / VAT N")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 6 — DOC 480 (Out-of-Scope Invoice) × Valid Transaction Types
# ─────────────────────────────────────────────────────────────────────────────
gen(36, "480", "Standard",   ["Z"],           "Out-of-Scope Invoice / Standard / VAT Z")
gen(37, "480", "Standard",   ["E"],           "Out-of-Scope Invoice / Standard / VAT E — TaxExemptionReasonCode")
gen(38, "480", "Standard",   ["O"],           "Out-of-Scope Invoice / Standard / VAT O")
gen(39, "480", "FTZ",        ["Z"],           "Out-of-Scope Invoice / FTZ / VAT Z")
gen(40, "480", "Continuous", ["Z"],           "Out-of-Scope Invoice / Continuous Supply / VAT Z")
gen(41, "480", "Agent",      ["O"],           "Out-of-Scope Invoice / Agent Sale / VAT O")
gen(42, "480", "eCommerce",  ["Z"],           "Out-of-Scope Invoice / E-Commerce / VAT Z — with Delivery")
gen(43, "480", "Exports",    ["Z"],           "Out-of-Scope Invoice / Exports / VAT Z — non-AE delivery")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 7 — DOC 81 (Out-of-Scope Credit Note) × Valid Transaction Types
# ─────────────────────────────────────────────────────────────────────────────
gen(44, "81",  "Standard",   ["Z"],           "Out-of-Scope Credit Note / Standard / VAT Z")
gen(45, "81",  "Standard",   ["E"],           "Out-of-Scope Credit Note / Standard / VAT E")
gen(46, "81",  "Standard",   ["O"],           "Out-of-Scope Credit Note / Standard / VAT O")
gen(47, "81",  "FTZ",        ["Z"],           "Out-of-Scope Credit Note / FTZ / VAT Z")
gen(48, "81",  "Exports",    ["Z"],           "Out-of-Scope Credit Note / Exports / VAT Z")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 8 — Multi-VAT: DOC 380 (Tax Invoice) — all 4 valid combos
# ─────────────────────────────────────────────────────────────────────────────
gen(49, "380", "Standard",   ["S", "Z"],           "Tax Invoice / Standard / VAT S+Z — 2 lines, 2 subtotals")
gen(50, "380", "Standard",   ["S", "AE"],          "Tax Invoice / Standard / VAT S+AE — AE triggers Buyer VAT TRN + NatureCode")
gen(51, "380", "Standard",   ["AE", "Z"],          "Tax Invoice / Standard / VAT AE+Z")
gen(52, "380", "Standard",   ["S", "AE", "Z"],     "Tax Invoice / Standard / VAT S+AE+Z — 3 lines, 3 subtotals")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 9 — Multi-VAT: DOC 381 (Tax Credit Note)
# ─────────────────────────────────────────────────────────────────────────────
gen(53, "381", "Standard",   ["S", "Z"],           "Tax Credit Note / Standard / VAT S+Z")
gen(54, "381", "Standard",   ["S", "AE"],          "Tax Credit Note / Standard / VAT S+AE")
gen(55, "381", "Standard",   ["AE", "Z"],          "Tax Credit Note / Standard / VAT AE+Z")
gen(56, "381", "Standard",   ["S", "AE", "Z"],     "Tax Credit Note / Standard / VAT S+AE+Z")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 10 — Multi-VAT: DOC 389 (Self-Billing Invoice) — all 8 valid combos
# ─────────────────────────────────────────────────────────────────────────────
gen(57, "389", "Standard",   ["S", "Z"],           "Self-Billing Invoice / Standard / VAT S+Z")
gen(58, "389", "Standard",   ["S", "AE"],          "Self-Billing Invoice / Standard / VAT S+AE")
gen(59, "389", "Standard",   ["S", "E"],           "Self-Billing Invoice / Standard / VAT S+E")
gen(60, "389", "Standard",   ["S", "O"],           "Self-Billing Invoice / Standard / VAT S+O")
gen(61, "389", "Standard",   ["AE", "Z"],          "Self-Billing Invoice / Standard / VAT AE+Z")
gen(62, "389", "Standard",   ["Z", "E"],           "Self-Billing Invoice / Standard / VAT Z+E")
gen(63, "389", "Standard",   ["Z", "O"],           "Self-Billing Invoice / Standard / VAT Z+O")
gen(64, "389", "Standard",   ["S", "AE", "Z"],     "Self-Billing Invoice / Standard / VAT S+AE+Z")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 11 — Multi-VAT: DOC 261 (Self-Billing Credit Note)
# ─────────────────────────────────────────────────────────────────────────────
gen(65, "261", "Standard",   ["S", "Z"],           "Self-Billing Credit Note / Standard / VAT S+Z")
gen(66, "261", "Standard",   ["S", "AE"],          "Self-Billing Credit Note / Standard / VAT S+AE")
gen(67, "261", "Standard",   ["S", "E"],           "Self-Billing Credit Note / Standard / VAT S+E")
gen(68, "261", "Standard",   ["Z", "E"],           "Self-Billing Credit Note / Standard / VAT Z+E")
gen(69, "261", "Standard",   ["Z", "O"],           "Self-Billing Credit Note / Standard / VAT Z+O")
gen(70, "261", "Standard",   ["S", "AE", "Z"],     "Self-Billing Credit Note / Standard / VAT S+AE+Z")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 12 — Multi-VAT: DOC 480 (Out-of-Scope Invoice) — all 4 valid combos
# ─────────────────────────────────────────────────────────────────────────────
gen(71, "480", "Standard",   ["Z", "E"],           "Out-of-Scope Invoice / Standard / VAT Z+E")
gen(72, "480", "Standard",   ["Z", "O"],           "Out-of-Scope Invoice / Standard / VAT Z+O")
gen(73, "480", "Standard",   ["E", "O"],           "Out-of-Scope Invoice / Standard / VAT E+O")
gen(74, "480", "Standard",   ["Z", "E", "O"],      "Out-of-Scope Invoice / Standard / VAT Z+E+O — 3 lines")

# ─────────────────────────────────────────────────────────────────────────────
#  CATEGORY 13 — Multi-VAT: DOC 81 (Out-of-Scope Credit Note) — all 4 valid combos
# ─────────────────────────────────────────────────────────────────────────────
gen(75, "81",  "Standard",   ["Z", "E"],           "Out-of-Scope Credit Note / Standard / VAT Z+E")
gen(76, "81",  "Standard",   ["Z", "O"],           "Out-of-Scope Credit Note / Standard / VAT Z+O")
gen(77, "81",  "Standard",   ["E", "O"],           "Out-of-Scope Credit Note / Standard / VAT E+O")
gen(78, "81",  "Standard",   ["Z", "E", "O"],      "Out-of-Scope Credit Note / Standard / VAT Z+E+O")


# ─────────────────────────────────────────────────────────────────────────────
print(f"\nGenerated {len(FILES)} positive-scenario XML files in: {OUT}\n")
print(f"{'#':<8} {'File':<62} Description")
print("-" * 140)
for i, (fname, desc) in enumerate(FILES, 1):
    print(f"{i:<8} {fname:<62} {desc}")
