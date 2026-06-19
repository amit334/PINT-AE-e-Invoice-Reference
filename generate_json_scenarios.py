#!/usr/bin/env python3
"""
Generate positive and negative JSON scenario files based on the sample.json schema.
  Seller endpoint : 1000454545 / Buyer endpoint : 1000464646

Run:  python generate_json_scenarios.py
Output:
  positive-json-scenarios/  (25 files)
  negative-json-scenarios/  (28 files)
"""

import json
import copy
from pathlib import Path

POS_OUT = Path(__file__).parent / "positive-json-scenarios"
NEG_OUT = Path(__file__).parent / "negative-json-scenarios"
POS_OUT.mkdir(exist_ok=True)
NEG_OUT.mkdir(exist_ok=True)

SELLER_EP  = "1000454545"
BUYER_EP   = "1000464646"
SELLER_VAT = "198765432102003"
BUYER_VAT  = "134567890123003"
SELLER_TL  = "112345678900003"
BUYER_TL   = "112345679000003"

POS_FILES, NEG_FILES = [], []

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def write_pos(name, doc, description):
    path = POS_OUT / name
    path.write_text(json.dumps(doc, indent=4, ensure_ascii=False), encoding="utf-8")
    POS_FILES.append((name, description))

def write_neg(name, doc, description):
    path = NEG_OUT / name
    path.write_text(json.dumps(doc, indent=4, ensure_ascii=False), encoding="utf-8")
    NEG_FILES.append((name, description))

def totals(line_sum, vat_amount, rounding=0.00):
    """Build the totals block. taxable == line_sum (no doc-level adj)."""
    with_vat = round(line_sum + vat_amount, 2)
    return {
        "sum_of_invoice_line_net_amount":         f"{line_sum:.2f}",
        "sum_of_allowances_on_document_level":    "0.00",
        "sum_of_charges_on_document_level":       "0.00",
        "invoice_total_amount_without_vat":       f"{line_sum:.2f}",
        "invoice_total_vat_amount":               f"{vat_amount:.2f}",
        "invoice_total_vat_amount_in_accounting_currency": f"{vat_amount:.2f}",
        "invoice_total_amount_with_vat":          f"{with_vat:.2f}",
        "paid_amount":                            "0.00",
        "rounding_amount":                        f"{rounding:.2f}",
        "amount_due_for_payment":                 f"{round(with_vat + rounding, 2):.2f}",
        "invoice_total_amount_with_vat_in_aed":   f"{with_vat:.2f}",
        "tax_included_indicator": False,
    }

def totals_with_adj(line_sum, doc_allow, doc_charge, vat_rate_pct, rounding=0.00):
    """Build totals when doc-level allowances/charges exist."""
    taxable   = round(line_sum - doc_allow + doc_charge, 2)
    vat_amt   = round(taxable * vat_rate_pct / 100, 2)
    with_vat  = round(taxable + vat_amt, 2)
    return {
        "sum_of_invoice_line_net_amount":         f"{line_sum:.2f}",
        "sum_of_allowances_on_document_level":    f"{doc_allow:.2f}",
        "sum_of_charges_on_document_level":       f"{doc_charge:.2f}",
        "invoice_total_amount_without_vat":       f"{taxable:.2f}",
        "invoice_total_vat_amount":               f"{vat_amt:.2f}",
        "invoice_total_vat_amount_in_accounting_currency": f"{vat_amt:.2f}",
        "invoice_total_amount_with_vat":          f"{with_vat:.2f}",
        "paid_amount":                            "0.00",
        "rounding_amount":                        f"{rounding:.2f}",
        "amount_due_for_payment":                 f"{round(with_vat + rounding, 2):.2f}",
        "invoice_total_amount_with_vat_in_aed":   f"{with_vat:.2f}",
        "tax_included_indicator": False,
    }

def vat_breakdown(code, taxable, rate):
    d = {
        "taxable_amount": f"{taxable:.2f}",
        "tax_amount":     f"{round(taxable * rate / 100, 2):.2f}",
        "vat_category_code": code,
        "tax_scheme_code": "VAT",
    }
    if code not in ("E", "O"):
        d["vat_category_rate"] = f"{rate:.2f}"
    if code == "E":
        d["vat_exemption_reason_code"] = "VATEX-AE-IBRZ"
    return d

def line(idx, name, description, qty, unit_price, net_amount,
         vat_code, vat_rate, line_incl_aed, vat_line_aed,
         allow=None, charge=None):
    l = {
        "line_id":    str(idx),
        "note":       None,
        "object_identifier": None,
        "object_identifier_scheme": None,
        "invoiced_quantity": f"{qty:.6f}",
        "invoiced_quantity_unit_of_measure_code": "C62",
        "line_net_amount": f"{net_amount:.2f}",
        "purchase_order_line_reference": None,
        "buyer_accounting_reference": None,
        "purchase_order_reference": "PO-2025-001",
        "despatch_advice_reference": None,
        "batch_number": None,
        "line_period_start_date": None,
        "line_period_end_date": None,
        "item_net_price": f"{unit_price:.2f}",
        "item_price_discount": "0.00",
        "item_gross_price": f"{unit_price:.2f}",
        "item_price_base_quantity": "1.000000",
        "item_price_base_quantity_unit_of_measure_code": "C62",
        "item_name": name,
        "item_description": description,
        "item_sellers_identifier": None,
        "item_buyers_identifier": None,
        "item_standard_identifier": None,
        "item_standard_identifier_scheme": None,
        "item_country_of_origin": "AE",
        "item_type": None,
        "type_of_goods_or_services": None,
        "line_amount_in_aed": f"{line_incl_aed:.2f}",
        "vat_line_amount_in_aed": f"{vat_line_aed:.2f}",
        "allowances": allow or [],
        "charges":    charge or [],
        "vat_info": [{
            "vat_category_code": vat_code,
            "vat_rate": f"{vat_rate:.2f}" if vat_code not in ("E", "O") else None,
            "tax_scheme": "VAT",
            "vat_exemption_reason_text": None,
            "vat_exemption_reason_code": "VATEX-AE-IBRZ" if vat_code == "E" else None,
        }],
        "attributes": [],
        "classifications": [],
        "service_accounting_codes": [],
    }
    return l

def ae_line(idx, name, description, net_amount):
    """AE (Reverse Charge) line — needs standardItemIdentification."""
    l = line(idx, name, description, 10, net_amount/10, net_amount,
             "AE", 0, net_amount, 0.00)
    l["item_standard_identifier"]        = f"RC-{idx:08d}"
    l["item_standard_identifier_scheme"] = "0160"
    l["type_of_goods_or_services"]       = "DL8.48.3.2"
    return l

def payment_means_30():
    return [{
        "payment_means_type_code": "30",
        "payment_means_text": "Credit transfer",
        "payment_instructions_id": None,
        "payment_account_identifier": "AE070331234567890123456",
        "payment_account_identifier_scheme": None,
        "payment_account_name": "Seller Account",
        "payment_service_provider_identifier": None,
        "payment_card_primary_account_number": None,
        "payment_card_holder_name": None,
        "mandate_reference_identifier": None,
        "bank_assigned_creditor_identifier": None,
        "debited_account_identifier": None,
        "account_address_line_1": None,
        "account_address_line_2": None,
        "account_address_line_3": None,
        "account_city": None,
        "account_post_code": None,
        "account_country_subdivision": None,
        "account_country_code": None,
        "remittance_information": [],
    }]

def seller_block(ep=SELLER_EP, vat=SELLER_VAT, tl=SELLER_TL,
                 name="Seller Legal Name LLC", city="Dubai",
                 subdiv="DXB", country="AE"):
    return {
        "name": name,
        "trading_name": "Seller Trading Co",
        "legal_registration_identifier": tl,
        "legal_registration_identifier_scheme": "0235",
        "vat_identifier": vat,
        "tax_scheme": "VAT",
        "tax_registration_identifier": None,
        "tax_registration_tax_scheme": None,
        "additional_legal_information": None,
        "electronic_address": ep,
        "electronic_address_scheme": "0235",
        "address_line_1": "Main Street",
        "address_line_2": None,
        "address_line_3": None,
        "city": city,
        "post_code": None,
        "country_subdivision": subdiv,
        "country_code": country,
        "contact_point": None,
        "contact_telephone_number": None,
        "contact_email_address": None,
        "authority_name": "Trade License issuing Authority",
        "legal_registration_identifier_type": "TL",
        "passport_issuing_country_code": None,
        "identifiers": [],
    }

def buyer_block(ep=BUYER_EP, vat=BUYER_VAT, tl=BUYER_TL,
                name="Buyer Legal Name LLC", city="Abu Dhabi",
                subdiv="AUH", country="AE", beneficiary=None):
    return {
        "name": name,
        "trading_name": "Buyer Trading Co",
        "identifier": None,
        "identifier_scheme": None,
        "legal_registration_identifier": tl,
        "legal_registration_identifier_scheme": "0235",
        "vat_identifier": vat,
        "tax_scheme": "VAT",
        "electronic_address": ep,
        "electronic_address_scheme": "0235",
        "address_line_1": "Al Khalidiyah Street",
        "address_line_2": None,
        "address_line_3": None,
        "city": city,
        "post_code": None,
        "country_subdivision": subdiv,
        "country_code": country,
        "contact_point": None,
        "contact_telephone_number": None,
        "contact_email_address": None,
        "beneficiary_identifier": beneficiary,
        "authority_name": "Trade License issuing Authority",
        "legal_registration_identifier_type": "TL",
        "passport_issuing_country_code": None,
    }

def base_invoice(seq, doc_type, txn_code, note="Tax Invoice"):
    is_sb  = doc_type in ("389", "261")
    is_cn  = doc_type in ("381", "261", "81")
    cust   = "urn:peppol:pint:selfbilling-1@ae-1" if is_sb else "urn:peppol:pint:billing-1@ae-1"
    prof   = "urn:peppol:bis:selfbilling" if is_sb else "urn:peppol:bis:billing"
    return {
        "issue_date": "2025-06-01",
        "invoice_type_code": doc_type,
        "invoice_currency_code": "AED",
        "tax_currency_code": None,
        "vat_point_date": None if is_cn else "2025-05-31",
        "payment_due_date": None if is_cn else "2025-06-15",
        "buyer_reference": f"PO-2025-{seq:03d}",
        "project_reference": None,
        "contract_document_reference": None,
        "purchase_order_reference": f"PO-2025-{seq:03d}",
        "sales_order_reference": None,
        "receipt_document_reference": None,
        "despatch_document_reference": None,
        "originator_document_reference": None,
        "additional_document_reference_id": None,
        "additional_document_reference_id_scheme": None,
        "buyer_accounting_reference": None,
        "invoice_note": note,
        "issue_time": "09:00:00",
        "transaction_type_code": txn_code,
        "discrepancy_response_code": "DL8.61.1.E" if is_cn else None,
        "currency_exchange_rate": None,
        "contract_value": None,
        "principal_identifier": None,
        "customs_reference_number": None,
        "process_control": {"profile_id": prof, "customization_id": cust},
        "seller": seller_block(),
        "buyer":  buyer_block(),
        "payee": None,
        "seller_tax_representative": None,
        "delivery": None,
        "totals": {},   # filled per scenario
        "preceding_invoice_references": [
            {"preceding_invoice_reference": "INV-2025-000", "preceding_invoice_issue_date": "2025-05-15"}
        ] if is_cn else [],
        "allowances": [],
        "charges": [],
        "vat_breakdowns": [],
        "supporting_documents": [],
        "payment_instructions": [] if is_cn else payment_means_30(),
        "terms": [{"payment_terms": "Net 14 days", "terms_amount": None,
                   "terms_installment_due_date": "2025-06-15",
                   "terms_payment_instructions_id": None}],
        "lines": [],
    }


# ══════════════════════════════════════════════════════════════════════════════
#  POSITIVE SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

# ── POS-001 : 380 / Standard / S ─────────────────────────────────────────────
d = base_invoice(1, "380", "00000000", "Tax Invoice - Standard 5%")
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Test Item [S]", "Standard rated supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-001-380-standard-vat-S.json", d,
          "Tax Invoice / Standard (00000000) / VAT S 5%")

# ── POS-002 : 380 / Standard / AE ────────────────────────────────────────────
d = base_invoice(2, "380", "00000000", "Tax Invoice - Reverse Charge")
d["vat_breakdowns"] = [vat_breakdown("AE", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [ae_line(1, "Test Item [AE]", "Reverse charge supply", 1000.00)]
write_pos("pos-002-380-standard-vat-AE.json", d,
          "Tax Invoice / Standard / VAT AE (Reverse Charge)")

# ── POS-003 : 380 / Standard / Z ─────────────────────────────────────────────
d = base_invoice(3, "380", "00000000", "Tax Invoice - Zero Rated")
d["vat_breakdowns"] = [vat_breakdown("Z", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [line(1, "Test Item [Z]", "Zero-rated supply",
                             10, 100.00, 1000.00, "Z", 0, 1000.00, 0.00)]
write_pos("pos-003-380-standard-vat-Z.json", d,
          "Tax Invoice / Standard / VAT Z (Zero-Rated)")

# ── POS-004 : 380 / FTZ / S  (with beneficiary) ──────────────────────────────
d = base_invoice(4, "380", "10000000", "Tax Invoice - Free Trade Zone")
d["buyer"]["beneficiary_identifier"] = "198765432100003"
d["delivery"] = {
    "delivery_location": {
        "address_line_1": "Jebel Ali Free Zone",
        "city": "Dubai", "country_subdivision": "DXB", "country_code": "AE"
    }
}
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Test Item [S]", "Standard rated FTZ supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-004-380-ftz-vat-S.json", d,
          "Tax Invoice / FTZ (10000000) / VAT S — beneficiary_identifier set")

# ── POS-005 : 380 / Deemed Supply / S (no due date, no payment means) ────────
d = base_invoice(5, "380", "01000000", "Tax Invoice - Deemed Supply")
d["payment_due_date"]   = None
d["payment_instructions"] = []
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Test Item [S]", "Deemed supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-005-380-deemed-vat-S.json", d,
          "Tax Invoice / Deemed Supply (01000000) / VAT S — no DueDate/PaymentMeans")

# ── POS-006 : 380 / Profit Margin / N ────────────────────────────────────────
d = base_invoice(6, "380", "00100000", "Tax Invoice - Profit Margin Scheme")
d["vat_point_date"]  = None    # no TaxPointDate for Margin
d["vat_breakdowns"]  = [vat_breakdown("N", 1000.00, 5)]
d["totals"]          = totals(1000.00, 50.00)
d["lines"]           = [line(1, "Test Item [N]", "Margin scheme supply",
                              10, 100.00, 1000.00, "N", 5, 1050.00, 50.00)]
write_pos("pos-006-380-margin-vat-N.json", d,
          "Tax Invoice / Profit Margin Scheme (00100000) / VAT N")

# ── POS-007 : 380 / Summary Invoice / S (with period) ────────────────────────
d = base_invoice(7, "380", "00010000", "Tax Invoice - Summary")
d["line_period_start_date"] = "2025-05-01"
d["line_period_end_date"]   = "2025-05-31"
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
ln = line(1, "Test Item [S]", "Summary period supply",
          10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)
ln["line_period_start_date"] = "2025-05-01"
ln["line_period_end_date"]   = "2025-05-31"
d["lines"] = [ln]
write_pos("pos-007-380-summary-vat-S.json", d,
          "Tax Invoice / Summary Invoice (00010000) / VAT S — with InvoicePeriod")

# ── POS-008 : 380 / Exports / Z (non-AE delivery) ────────────────────────────
d = base_invoice(8, "380", "00000001", "Tax Invoice - Exports")
d["delivery"] = {
    "delivery_location": {
        "address_line_1": "456 Main Street",
        "city": "New York", "country_subdivision": "NY", "country_code": "US"
    },
    "delivery_terms": {"id": "CIF", "scheme_id": "Incoterms"}
}
d["customs_reference_number"] = "CRN-2025-001"
d["vat_breakdowns"] = [vat_breakdown("Z", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [line(1, "Test Item [Z]", "Zero-rated export supply",
                             10, 100.00, 1000.00, "Z", 0, 1000.00, 0.00)]
write_pos("pos-008-380-exports-vat-Z.json", d,
          "Tax Invoice / Exports (00000001) / VAT Z — non-AE delivery, CIF terms")

# ── POS-009 : 380 / eCommerce / S (UAE delivery) ─────────────────────────────
d = base_invoice(9, "380", "00000010", "Tax Invoice - eCommerce")
d["delivery"] = {
    "delivery_location": {
        "address_line_1": "Al Barsha",
        "city": "Dubai", "country_subdivision": "DXB", "country_code": "AE"
    }
}
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Test Item [S]", "E-commerce supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-009-380-ecommerce-vat-S.json", d,
          "Tax Invoice / eCommerce (00000010) / VAT S — UAE delivery address")

# ── POS-010 : 380 / Agent / S (with principal) ───────────────────────────────
d = base_invoice(10, "380", "00000100", "Tax Invoice - Agent Sale")
d["principal_identifier"] = "134567890120003"
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Test Item [S]", "Agent supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-010-380-agent-vat-S.json", d,
          "Tax Invoice / Disclosed Agent (00000100) / VAT S — principal_identifier set")

# ── POS-011 : 380 / Continuous / S ───────────────────────────────────────────
d = base_invoice(11, "380", "00001000", "Tax Invoice - Continuous Supply")
d["line_period_start_date"] = "2025-05-01"
d["line_period_end_date"]   = "2025-06-01"
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Test Item [S]", "Continuous supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-011-380-continuous-vat-S.json", d,
          "Tax Invoice / Continuous Supply (00001000) / VAT S")

# ── POS-012 : 380 / Standard / S — Multi-line (3 lines) ──────────────────────
d = base_invoice(12, "380", "00000000", "Tax Invoice - Multiple Lines")
d["vat_breakdowns"] = [vat_breakdown("S", 1500.00, 5)]
d["totals"]         = totals(1500.00, 75.00)
d["lines"] = [
    line(1, "Product A", "Standard rated supply A", 5, 100.00, 500.00, "S", 5, 525.00, 25.00),
    line(2, "Product B", "Standard rated supply B", 5, 100.00, 500.00, "S", 5, 525.00, 25.00),
    line(3, "Product C", "Standard rated supply C", 5, 100.00, 500.00, "S", 5, 525.00, 25.00),
]
write_pos("pos-012-380-standard-vat-S-multiline.json", d,
          "Tax Invoice / Standard / VAT S — 3 invoice lines totalling 1500 AED")

# ── POS-013 : 380 / Standard / S — Doc-level allowance + charge ──────────────
d = base_invoice(13, "380", "00000000", "Tax Invoice - With Allowance and Charge")
d["allowances"] = [{
    "amount": "25.00", "base_amount": "1000.00", "percentage": "2.50",
    "vat_category_code": "S", "tax_scheme_code": "VAT", "vat_rate": "5.00",
    "reason": "Special discount", "reason_code": "100",
    "vat_exemption_reason_code": None, "vat_exemption_reason_text": None,
}]
d["charges"] = [{
    "amount": "40.00", "base_amount": "1000.00", "percentage": "4.00",
    "vat_category_code": "S", "tax_scheme_code": "VAT", "vat_rate": "5.00",
    "reason": "Urgent delivery", "reason_code": "AAT",
    "vat_exemption_reason_code": None, "vat_exemption_reason_text": None,
}]
d["vat_breakdowns"] = [vat_breakdown("S", 1015.00, 5)]
d["totals"]         = totals_with_adj(1000.00, 25.00, 40.00, 5)
d["lines"]          = [line(1, "Test Item [S]", "Standard rated supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-013-380-standard-vat-S-with-adj.json", d,
          "Tax Invoice / Standard / VAT S — doc-level allowance (-25) + charge (+40)")

# ── POS-014 : 380 / Standard / Multi-VAT S+Z ─────────────────────────────────
d = base_invoice(14, "380", "00000000", "Tax Invoice - Mixed S+Z")
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5), vat_breakdown("Z", 1000.00, 0)]
d["totals"]         = totals(2000.00, 50.00)
d["lines"] = [
    line(1, "Item 1 [S]", "Standard rated supply",  10, 100.00, 1000.00, "S", 5, 1050.00, 50.00),
    line(2, "Item 2 [Z]", "Zero-rated supply",       10, 100.00, 1000.00, "Z", 0, 1000.00,  0.00),
]
write_pos("pos-014-380-standard-vat-S-Z.json", d,
          "Tax Invoice / Standard / VAT S+Z — 2 lines, 2 VAT breakdowns")

# ── POS-015 : 380 / Standard / Multi-VAT S+AE ────────────────────────────────
d = base_invoice(15, "380", "00000000", "Tax Invoice - Mixed S+AE")
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5), vat_breakdown("AE", 1000.00, 0)]
d["totals"]         = totals(2000.00, 50.00)
d["lines"] = [
    line(1, "Item 1 [S]",  "Standard rated supply",  10, 100.00, 1000.00, "S",  5, 1050.00, 50.00),
    ae_line(2, "Item 2 [AE]", "Reverse charge supply", 1000.00),
]
write_pos("pos-015-380-standard-vat-S-AE.json", d,
          "Tax Invoice / Standard / VAT S+AE — 2 lines, buyer VAT TRN required for AE")

# ── POS-016 : 381 / Standard / S — Tax Credit Note ───────────────────────────
d = base_invoice(16, "381", "00000000", "Tax Credit Note")
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Item [S]", "Standard rated supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-016-381-standard-vat-S.json", d,
          "Tax Credit Note / Standard / VAT S — DiscrepancyResponse + BillingReference")

# ── POS-017 : 381 / Standard / AE ────────────────────────────────────────────
d = base_invoice(17, "381", "00000000", "Tax Credit Note - Reverse Charge")
d["vat_breakdowns"] = [vat_breakdown("AE", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [ae_line(1, "Item [AE]", "Reverse charge credit", 1000.00)]
write_pos("pos-017-381-standard-vat-AE.json", d,
          "Tax Credit Note / Standard / VAT AE")

# ── POS-018 : 381 / Standard / Z ─────────────────────────────────────────────
d = base_invoice(18, "381", "00000000", "Tax Credit Note - Zero Rated")
d["vat_breakdowns"] = [vat_breakdown("Z", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [line(1, "Item [Z]", "Zero-rated credit",
                             10, 100.00, 1000.00, "Z", 0, 1000.00, 0.00)]
write_pos("pos-018-381-standard-vat-Z.json", d,
          "Tax Credit Note / Standard / VAT Z")

# ── POS-019 : 381 / FTZ / S ──────────────────────────────────────────────────
d = base_invoice(19, "381", "10000000", "Tax Credit Note - FTZ")
d["buyer"]["beneficiary_identifier"] = "198765432100003"
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Item [S]", "FTZ credit note",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-019-381-ftz-vat-S.json", d,
          "Tax Credit Note / FTZ (10000000) / VAT S")

# ── POS-020 : 389 / Standard / S — Self-Billing Invoice ──────────────────────
d = base_invoice(20, "389", "00000000", "Self-Billing Invoice")
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Item [S]", "Self-billed standard supply",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-020-389-standard-vat-S.json", d,
          "Self-Billing Invoice / Standard / VAT S — selfbilling-1@ae-1 customization")

# ── POS-021 : 389 / Standard / E — Exempt ────────────────────────────────────
d = base_invoice(21, "389", "00000000", "Self-Billing Invoice - Exempt")
d["vat_breakdowns"] = [vat_breakdown("E", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"] = [line(1, "Exempt Item [E]", "Exempt supply",
                   10, 100.00, 1000.00, "E", 0, 1000.00, 0.00)]
write_pos("pos-021-389-standard-vat-E.json", d,
          "Self-Billing Invoice / Standard / VAT E — TaxExemptionReasonCode VATEX-AE-IBRZ")

# ── POS-022 : 389 / Standard / O ─────────────────────────────────────────────
d = base_invoice(22, "389", "00000000", "Self-Billing Invoice - Out of Scope")
d["vat_breakdowns"] = [vat_breakdown("O", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [line(1, "Item [O]", "Not subject to VAT",
                             10, 100.00, 1000.00, "O", 0, 1000.00, 0.00)]
write_pos("pos-022-389-standard-vat-O.json", d,
          "Self-Billing Invoice / Standard / VAT O (Not Subject to VAT)")

# ── POS-023 : 261 / Standard / S — Self-Billing Credit Note ──────────────────
d = base_invoice(23, "261", "00000000", "Self-Billing Credit Note")
d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
d["totals"]         = totals(1000.00, 50.00)
d["lines"]          = [line(1, "Item [S]", "Self-billed credit",
                             10, 100.00, 1000.00, "S", 5, 1050.00, 50.00)]
write_pos("pos-023-261-standard-vat-S.json", d,
          "Self-Billing Credit Note / Standard / VAT S")

# ── POS-024 : 480 / Standard / Z — Out-of-Scope Invoice ─────────────────────
d = base_invoice(24, "480", "00000000", "Commercial Invoice (Out of Scope)")
d["vat_point_date"]       = None   # no TaxPointDate for 480 with Z
d["vat_breakdowns"] = [vat_breakdown("Z", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [line(1, "Item [Z]", "Zero-rated OOS supply",
                             10, 100.00, 1000.00, "Z", 0, 1000.00, 0.00)]
write_pos("pos-024-480-standard-vat-Z.json", d,
          "Out-of-Scope Invoice (480) / Standard / VAT Z")

# ── POS-025 : 81 / Standard / E — Out-of-Scope Credit Note ──────────────────
d = base_invoice(25, "81",  "00000000", "Commercial Credit Note (Out of Scope)")
d["vat_breakdowns"] = [vat_breakdown("E", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [line(1, "Item [E]", "Exempt OOS credit",
                             10, 100.00, 1000.00, "E", 0, 1000.00, 0.00)]
write_pos("pos-025-081-standard-vat-E.json", d,
          "Out-of-Scope Credit Note (81) / Standard / VAT E")


# ══════════════════════════════════════════════════════════════════════════════
#  NEGATIVE SCENARIOS  — each starts from a valid base then breaks one thing
# ══════════════════════════════════════════════════════════════════════════════

def valid_base():
    """Return a fresh deep-copy of a minimal valid 380/S invoice."""
    d = base_invoice(99, "380", "00000000", "Tax Invoice")
    d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
    d["totals"]         = totals(1000.00, 50.00)
    d["lines"]          = [line(1, "Test Item", "Supply", 10, 100.00, 1000.00,
                                "S", 5, 1050.00, 50.00)]
    return d

def valid_cn_base():
    d = base_invoice(99, "381", "00000000", "Tax Credit Note")
    d["vat_breakdowns"] = [vat_breakdown("S", 1000.00, 5)]
    d["totals"]         = totals(1000.00, 50.00)
    d["lines"]          = [line(1, "Test Item", "Supply", 10, 100.00, 1000.00,
                                "S", 5, 1050.00, 50.00)]
    return d


# ── NEG-001 : Missing seller name ────────────────────────────────────────────
d = valid_base(); del d["seller"]["name"]
write_neg("neg-001-missing-seller-name.json", d,
          "Seller name (IBT-027) omitted — required RegistrationName")

# ── NEG-002 : Missing seller VAT identifier ───────────────────────────────────
d = valid_base(); del d["seller"]["vat_identifier"]
write_neg("neg-002-missing-seller-vat.json", d,
          "Seller vat_identifier (IBT-031 / BTAE-11) omitted")

# ── NEG-003 : Missing seller electronic_address (endpoint) ───────────────────
d = valid_base(); del d["seller"]["electronic_address"]
write_neg("neg-003-missing-seller-endpoint.json", d,
          "Seller electronic_address / EndpointID (IBT-034) omitted")

# ── NEG-004 : Missing seller trade license ───────────────────────────────────
d = valid_base(); del d["seller"]["legal_registration_identifier"]
write_neg("neg-004-missing-seller-trade-license.json", d,
          "Seller legal_registration_identifier / Trade License (BTAE-12/15) omitted")

# ── NEG-005 : Seller country not AE ──────────────────────────────────────────
d = valid_base(); d["seller"]["country_code"] = "GB"
write_neg("neg-005-seller-country-not-ae.json", d,
          "Seller country_code is 'GB' instead of 'AE' (BTAE-07)")

# ── NEG-006 : Missing buyer name ─────────────────────────────────────────────
d = valid_base(); del d["buyer"]["name"]
write_neg("neg-006-missing-buyer-name.json", d,
          "Buyer name (IBT-044) omitted")

# ── NEG-007 : Missing buyer electronic_address ────────────────────────────────
d = valid_base(); del d["buyer"]["electronic_address"]
write_neg("neg-007-missing-buyer-endpoint.json", d,
          "Buyer electronic_address / EndpointID (IBT-049) omitted")

# ── NEG-008 : Missing buyer trade license ────────────────────────────────────
d = valid_base(); del d["buyer"]["legal_registration_identifier"]
write_neg("neg-008-missing-buyer-trade-license.json", d,
          "Buyer legal_registration_identifier / Trade License (BTAE-13/16) omitted")

# ── NEG-009 : Missing invoice_type_code ──────────────────────────────────────
d = valid_base(); del d["invoice_type_code"]
write_neg("neg-009-missing-invoice-type-code.json", d,
          "invoice_type_code (IBT-003) omitted entirely")

# ── NEG-010 : Missing issue_date ─────────────────────────────────────────────
d = valid_base(); del d["issue_date"]
write_neg("neg-010-missing-issue-date.json", d,
          "issue_date (IBT-002) omitted entirely")

# ── NEG-011 : Missing transaction_type_code (BTAE-02) ────────────────────────
d = valid_base(); del d["transaction_type_code"]
write_neg("neg-011-missing-transaction-type-code.json", d,
          "transaction_type_code / ProfileExecutionID (BTAE-02) omitted")

# ── NEG-012 : Invalid invoice_type_code ──────────────────────────────────────
d = valid_base(); d["invoice_type_code"] = "999"
write_neg("neg-012-invalid-invoice-type-code.json", d,
          "invoice_type_code '999' is not a valid PINT AE document type")

# ── NEG-013 : Invalid VAT category code ──────────────────────────────────────
d = valid_base()
d["vat_breakdowns"][0]["vat_category_code"] = "X"
d["lines"][0]["vat_info"][0]["vat_category_code"] = "X"
write_neg("neg-013-invalid-vat-category-code.json", d,
          "VAT category code 'X' is not a valid PINT AE code (S/AE/Z/E/O/N)")

# ── NEG-014 : Wrong VAT rate for S (15% instead of 5%) ───────────────────────
d = valid_base()
d["vat_breakdowns"][0]["vat_category_rate"] = "15.00"
d["lines"][0]["vat_info"][0]["vat_rate"] = "15.00"
write_neg("neg-014-wrong-vat-rate-for-s.json", d,
          "VAT category S has rate 15.00 — UAE standard rate is 5%")

# ── NEG-015 : Tax total amount mismatch ──────────────────────────────────────
d = valid_base()
d["totals"]["invoice_total_vat_amount"] = "99.00"
d["totals"]["invoice_total_amount_with_vat"] = "1099.00"
d["totals"]["amount_due_for_payment"] = "1099.00"
d["totals"]["invoice_total_amount_with_vat_in_aed"] = "1099.00"
write_neg("neg-015-tax-total-mismatch.json", d,
          "invoice_total_vat_amount (99.00) does not equal 5% of 1000.00 (should be 50.00)")

# ── NEG-016 : Invoice total amount without VAT mismatch ──────────────────────
d = valid_base()
d["totals"]["invoice_total_amount_without_vat"] = "2000.00"
d["totals"]["invoice_total_amount_with_vat"] = "2050.00"
d["totals"]["amount_due_for_payment"] = "2050.00"
write_neg("neg-016-invoice-total-without-vat-mismatch.json", d,
          "invoice_total_amount_without_vat (2000.00) != sum of line net amounts (1000.00)")

# ── NEG-017 : PayableAmount mismatch ─────────────────────────────────────────
d = valid_base(); d["totals"]["amount_due_for_payment"] = "500.00"
write_neg("neg-017-payable-amount-mismatch.json", d,
          "amount_due_for_payment (500.00) != invoice_total_amount_with_vat (1050.00)")

# ── NEG-018 : Credit note without discrepancy_response_code ──────────────────
d = valid_cn_base(); d["discrepancy_response_code"] = None
write_neg("neg-018-cn-missing-discrepancy-response.json", d,
          "Credit note discrepancy_response_code (BTAE-03) is null — mandatory")

# ── NEG-019 : Credit note without preceding_invoice_references ───────────────
d = valid_cn_base(); d["preceding_invoice_references"] = []
write_neg("neg-019-cn-missing-billing-reference.json", d,
          "Credit note preceding_invoice_references (IBG-01) is empty — mandatory")

# ── NEG-020 : Negative line net amount ───────────────────────────────────────
d = valid_base(); d["lines"][0]["line_net_amount"] = "-1000.00"
write_neg("neg-020-negative-line-amount.json", d,
          "line_net_amount is -1000.00 — use Credit Note for negative amounts")

# ── NEG-021 : Zero invoiced_quantity ─────────────────────────────────────────
d = valid_base(); d["lines"][0]["invoiced_quantity"] = "0.000000"
write_neg("neg-021-zero-quantity.json", d,
          "invoiced_quantity is 0 — quantity must be positive")

# ── NEG-022 : Invalid date format ────────────────────────────────────────────
d = valid_base(); d["issue_date"] = "01/06/2025"
write_neg("neg-022-invalid-date-format.json", d,
          "issue_date in DD/MM/YYYY format — must be YYYY-MM-DD (ISO 8601)")

# ── NEG-023 : No invoice lines ───────────────────────────────────────────────
d = valid_base(); d["lines"] = []
write_neg("neg-023-no-invoice-lines.json", d,
          "lines array is empty — at least one invoice line is required")

# ── NEG-024 : Missing vat_breakdowns ─────────────────────────────────────────
d = valid_base(); d["vat_breakdowns"] = []
write_neg("neg-024-missing-vat-breakdowns.json", d,
          "vat_breakdowns array is empty — at least one TaxSubtotal required")

# ── NEG-025 : Margin scheme with VAT S (should be N) ─────────────────────────
d = valid_base(); d["transaction_type_code"] = "00100000"
d["process_control"]["customization_id"] = "urn:peppol:pint:billing-1@ae-1"
write_neg("neg-025-margin-scheme-wrong-vat.json", d,
          "Profit Margin Scheme (00100000) requires VAT N, but VAT S is used")

# ── NEG-026 : VAT AE without buyer VAT identifier ────────────────────────────
d = valid_base()
d["vat_breakdowns"] = [vat_breakdown("AE", 1000.00, 0)]
d["totals"]         = totals(1000.00, 0.00)
d["lines"]          = [ae_line(1, "AE Item", "Reverse charge", 1000.00)]
del d["buyer"]["vat_identifier"]   # mandatory when VAT=AE
write_neg("neg-026-ae-vat-missing-buyer-vat.json", d,
          "VAT AE (Reverse Charge) requires buyer vat_identifier — omitted here")

# ── NEG-027 : Script injection in item_name ───────────────────────────────────
d = valid_base()
d["lines"][0]["item_name"] = "<script>alert('XSS')</script>"
write_neg("neg-027-script-injection-item-name.json", d,
          "Script tag injected in item_name — validator/converter should neutralise")

# ── NEG-028 : Seller city missing (street address incomplete) ─────────────────
d = valid_base(); del d["seller"]["city"]
write_neg("neg-028-missing-seller-city.json", d,
          "Seller city (IBT-037 / BTAE-05) omitted from address")


# ══════════════════════════════════════════════════════════════════════════════
#  PRINT SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print(f"\nPositive: {len(POS_FILES)} files -> {POS_OUT}")
print(f"Negative: {len(NEG_FILES)} files -> {NEG_OUT}")

print(f"\n{'#':<6} {'File':<52} Description")
print("POSITIVE SCENARIOS")
print("-" * 115)
for i, (f, d) in enumerate(POS_FILES, 1):
    print(f"  {i:<4} {f:<52} {d}")

print("\nNEGATIVE SCENARIOS")
print("-" * 115)
for i, (f, d) in enumerate(NEG_FILES, 1):
    print(f"  {i:<4} {f:<52} {d}")
