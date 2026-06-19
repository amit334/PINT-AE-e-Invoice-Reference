#!/usr/bin/env python3
"""
PINT AE JSON Generator + JSON→XML converter.
Uses the new PINT AE JSON schema (snake_case, flat structure matching sample.json).
"""

import json
import uuid
from datetime import date, timedelta
from decimal import Decimal
from lxml import etree

from generate_xml import (
    DOC_INFO, TRN_FLAGS, FX_RATES, VAT_CFG,
    BILLING_URN, SELF_BILLING_URN,
    INV_NS, CN_NS, CAC, CBC,
    _fmt, _r, _trn, _sub,
)

# VAT rates as shown in the new JSON format (from seller's perspective)
_VAT_RATE_OUT = {
    "S":  "5.00",
    "Z":  "0.00",
    "E":  None,          # no Percent element
    "O":  None,          # no Percent element
    "AE": "0.00",        # buyer accounts for VAT
    "N":  "5.00",        # margin scheme rate shown, but line IPE TaxAmount = 0
}



def generate_json(
    doc_type: str,
    vat_categories: list,
    transaction_type: str = "Standard",
    supplier_endpoint_id: str = "",
    supplier_endpoint_scheme: str = "0235",
    buyer_endpoint_id: str = "",
    buyer_endpoint_scheme: str = "0235",
    currency: str = "AED",
    supplier_name: str = "",
    buyer_name: str = "",
    supplier_vat: str = "",
    buyer_vat: str = "",
    supplier_tl: str = "",
    buyer_tl: str = "",
    item_type: str = "S",
    ftz_beneficiary_id: str = "",
    agent_principal_id: str = "",
) -> str:

    info       = DOC_INFO[doc_type]
    is_inv     = info["is_inv"]
    is_sb      = info["is_sb"]
    is_cn      = not is_inv
    is_export  = transaction_type == "Exports"
    is_margin  = transaction_type == "Margin"
    is_foreign = currency != "AED"

    supplier_endpoint_id = supplier_endpoint_id or _trn()
    buyer_endpoint_id    = buyer_endpoint_id    or _trn()
    supplier_vat         = supplier_vat         or _trn()
    buyer_vat            = buyer_vat            or _trn()
    supplier_tl          = supplier_tl          or _trn()
    buyer_tl             = buyer_tl             or _trn()
    supplier_name        = supplier_name        or "Seller Legal Name LLC"
    buyer_name           = buyer_name           or "Buyer Legal Name LLC"
    ftz_beneficiary_id   = ftz_beneficiary_id   or _trn()
    if not agent_principal_id:
        agent_principal_id = f"1{_r(12)}03"
        while agent_principal_id == supplier_vat:
            agent_principal_id = f"1{_r(12)}03"

    today        = date.today()
    issue_date   = today.isoformat()
    tax_point    = (today - timedelta(days=1)).isoformat()
    due_date     = (today + timedelta(days=14)).isoformat()
    prior_date   = (today - timedelta(days=7)).isoformat()
    period_start = (today - timedelta(days=30)).isoformat()
    flags        = TRN_FLAGS.get(transaction_type, "00000000")
    curr         = currency

    LINE_AMT = Decimal("1000.00")
    UNIT_PRC = Decimal("100.00")

    # ── Lines ─────────────────────────────────────────────────────────────────
    po_line = f"PO-{_r(6)}"
    lines_out = []
    subtotals  = {}   # cat → {taxable, doc_tax, pct, has_rate}

    for i, cat in enumerate(vat_categories, 1):
        cfg      = VAT_CFG[cat]
        vat_rate = _VAT_RATE_OUT[cat]           # shown in vat_info / vat_breakdown
        # line_tax: IPE-level tax (0 for margin/RC/Z/O/E; actual for S)
        line_tax = Decimal("0.00") if (cfg["line_tax_is_zero"] or not cfg["has_pct"]) \
                   else (LINE_AMT * cfg["pct"] / 100).quantize(Decimal("0.01"))
        # doc_tax: document-level tax for vat_breakdown
        # AE → buyer pays (ibr-105-ae); N → must be 0 (ibr-108-ae margin scheme)
        doc_tax  = (LINE_AMT * cfg["pct"] / 100).quantize(Decimal("0.01")) \
                   if cfg["has_pct"] and cat not in ("AE", "N") else Decimal("0.00")

        vat_info_entry = {
            "vat_category_code": cat,
            "vat_rate": vat_rate,
            "tax_scheme": "VAT",
            "vat_exemption_reason_text": None,
            "vat_exemption_reason_code": "VATEX-AE-IBRZ" if cat == "E" else None,
        }

        vat_line_aed = line_tax if not is_foreign else \
                       (line_tax * FX_RATES.get(curr, Decimal("3.67285"))).quantize(Decimal("0.01"))
        line_aed = (LINE_AMT if is_foreign else LINE_AMT) + vat_line_aed

        line = {
            "line_id": str(i),
            "note": None,
            "object_identifier": None,
            "object_identifier_scheme": None,
            "invoiced_quantity": "10.000000",
            "invoiced_quantity_unit_of_measure_code": "C62",
            "line_net_amount": _fmt(LINE_AMT),
            "purchase_order_line_reference": None,
            "buyer_accounting_reference": None,
            "purchase_order_reference": po_line,
            "despatch_advice_reference": None,
            "batch_number": None,
            "line_period_start_date": None,
            "line_period_end_date": None,
            "item_net_price": _fmt(UNIT_PRC),
            "item_price_discount": "0.00",
            "item_gross_price": _fmt(UNIT_PRC),
            "item_price_base_quantity": "1.000000",
            "item_price_base_quantity_unit_of_measure_code": "C62",
            "item_name": f"Test Item [{cat}]",
            "item_description": f"{cat}-rated supply — generated test instance",
            "item_sellers_identifier": None,
            "item_buyers_identifier": None,
            "item_standard_identifier": f"RC-{_r(8)}" if cat == "AE" else None,
            "item_standard_identifier_scheme": "0160" if cat == "AE" else None,
            "item_country_of_origin": "AE",
            "item_type": None,
            "type_of_goods_or_services": "DL8.48.3.2" if cat == "AE" else None,
            "line_amount_in_aed": _fmt(line_aed),
            "vat_line_amount_in_aed": None if cat == "E" else _fmt(vat_line_aed),
            "allowances": [],
            "charges": [],
            "vat_info": [vat_info_entry],
            "attributes": [],
            "classifications": [],
            "service_accounting_codes": [],
        }

        if transaction_type in ("Summary", "Continuous"):
            line["line_period_start_date"] = period_start
            line["line_period_end_date"]   = issue_date

        lines_out.append(line)

        if cat not in subtotals:
            subtotals[cat] = {
                "taxable":  Decimal("0"),
                "doc_tax":  Decimal("0"),
                "pct":      vat_rate,
                "has_rate": vat_rate is not None,
                "exemption_code": "VATEX-AE-IBRZ" if cat == "E" else None,
            }
        subtotals[cat]["taxable"]  += LINE_AMT
        subtotals[cat]["doc_tax"]  += doc_tax

    total_line_ext = sum(Decimal(l["line_net_amount"]) for l in lines_out)
    total_doc_tax  = sum(v["doc_tax"] for v in subtotals.values())
    tax_incl       = total_line_ext + total_doc_tax
    payable        = tax_incl

    # ── VAT breakdowns ────────────────────────────────────────────────────────
    vat_breakdowns = []
    for cat, st in subtotals.items():
        bd = {
            "taxable_amount": _fmt(st["taxable"]),
            "tax_amount":     _fmt(st["doc_tax"]),
            "vat_category_code": cat,
            "tax_scheme_code": "VAT",
        }
        if st["has_rate"]:
            bd["vat_category_rate"] = st["pct"]
        if st["exemption_code"]:
            bd["vat_exemption_reason_code"] = st["exemption_code"]
        vat_breakdowns.append(bd)

    # ── AED equivalents for foreign currency ──────────────────────────────────
    rate_val    = FX_RATES.get(curr, Decimal("3.67285")) if is_foreign else Decimal("1")
    tax_aed     = (total_doc_tax * rate_val).quantize(Decimal("0.01")) if is_foreign else total_doc_tax
    incl_aed    = (tax_incl * rate_val).quantize(Decimal("0.01")) if is_foreign else tax_incl

    # ── Document ──────────────────────────────────────────────────────────────
    po_ref = f"PO-{_r(6)}"
    doc = {
        "issue_date":                          issue_date,
        "invoice_type_code":                   doc_type,
        "invoice_currency_code":               curr,
        "tax_currency_code":                   "AED" if is_foreign else None,
        "vat_point_date":                      None if is_margin else (tax_point if is_inv else None),
        "payment_due_date":                    due_date if is_inv else None,
        "buyer_reference":                     po_ref,
        "project_reference":                   None,
        "contract_document_reference":         None,
        "purchase_order_reference":            po_ref,
        "sales_order_reference":               None,
        "receipt_document_reference":          None,
        "despatch_document_reference":         None,
        "originator_document_reference":       None,
        "additional_document_reference_id":    None,
        "additional_document_reference_id_scheme": None,
        "buyer_accounting_reference":          None,
        "invoice_note":                        info["label"],
        "issue_time":                          "09:00:00",
        "transaction_type_code":               flags,
        "discrepancy_response_code":           "DL8.61.1.E" if is_cn else None,
        "currency_exchange_rate":              float(rate_val) if is_foreign else None,
        "contract_value":                      None,
        "principal_identifier":                agent_principal_id if transaction_type == "Agent" else None,
        "customs_reference_number":            None,
        "process_control": {
            "profile_id":       "urn:peppol:bis:selfbilling" if is_sb else "urn:peppol:bis:billing",
            "customization_id": SELF_BILLING_URN if is_sb else BILLING_URN,
        },
        "seller": {
            "name":                              supplier_name,
            "trading_name":                      f"{supplier_name} Trading Co",
            "legal_registration_identifier":     supplier_tl,
            "legal_registration_identifier_scheme": "0235",
            "vat_identifier":                    supplier_vat,
            "tax_scheme":                        "VAT",
            "tax_registration_identifier":       None,
            "tax_registration_tax_scheme":       None,
            "additional_legal_information":      None,
            "electronic_address":                supplier_endpoint_id,
            "electronic_address_scheme":         supplier_endpoint_scheme,
            "address_line_1":                    "Sheikh Zayed Road",
            "address_line_2":                    None,
            "address_line_3":                    None,
            "city":                              "Dubai",
            "post_code":                         None,
            "country_subdivision":               "DXB",
            "country_code":                      "AE",
            "contact_point":                     None,
            "contact_telephone_number":          None,
            "contact_email_address":             None,
            "authority_name":                    "Trade License issuing Authority",
            "legal_registration_identifier_type": "TL",
            "passport_issuing_country_code":     None,
            "identifiers":                       [],
        },
        "buyer": {
            "name":                              buyer_name,
            "trading_name":                      f"{buyer_name} Trading Co",
            "identifier":                        None,
            "identifier_scheme":                 None,
            "legal_registration_identifier":     buyer_tl,
            "legal_registration_identifier_scheme": "0235",
            "vat_identifier":                    None if is_export else buyer_vat,
            "tax_scheme":                        None if is_export else "VAT",
            "electronic_address":                buyer_endpoint_id,
            "electronic_address_scheme":         buyer_endpoint_scheme,
            "address_line_1":                    "123 Export Street" if is_export else "Al Khalidiyah Street",
            "address_line_2":                    None,
            "address_line_3":                    None,
            "city":                              "London" if is_export else "Abu Dhabi",
            "post_code":                         None,
            "country_subdivision":               "ENG" if is_export else "AUH",
            "country_code":                      "GB" if is_export else "AE",
            "contact_point":                     None,
            "contact_telephone_number":          None,
            "contact_email_address":             None,
            "beneficiary_identifier":            ftz_beneficiary_id if transaction_type == "FTZ" else None,
            "authority_name":                    "Trade License issuing Authority",
            "legal_registration_identifier_type": "TL",
            "passport_issuing_country_code":     None,
        },
        "payee": None,
        "seller_tax_representative": None,
        "delivery": None,
        "totals": {
            "sum_of_invoice_line_net_amount":              _fmt(total_line_ext),
            "sum_of_allowances_on_document_level":         "0.00",
            "sum_of_charges_on_document_level":            "0.00",
            "invoice_total_amount_without_vat":            _fmt(total_line_ext),
            "invoice_total_vat_amount":                    _fmt(total_doc_tax),
            "invoice_total_vat_amount_in_accounting_currency": _fmt(tax_aed),
            "invoice_total_amount_with_vat":               _fmt(tax_incl),
            "paid_amount":                                 "0.00",
            "rounding_amount":                             "0.00",
            "amount_due_for_payment":                      _fmt(payable),
            "invoice_total_amount_with_vat_in_aed":        _fmt(incl_aed),
            "tax_included_indicator":                      False,
        },
        "preceding_invoice_references": [
            {"preceding_invoice_reference": f"INV-{_r(8)}", "preceding_invoice_issue_date": prior_date}
        ] if is_cn else [],
        "allowances":          [],
        "charges":             [],
        "vat_breakdowns":      vat_breakdowns,
        "supporting_documents": [],
        "payment_instructions": [] if (is_cn or transaction_type == "Deemed") else [
            {
                "payment_means_type_code":                 "30",
                "payment_means_text":                      "Credit transfer",
                "payment_instructions_id":                 None,
                "payment_account_identifier":              "AE070331234567890123456",
                "payment_account_identifier_scheme":       None,
                "payment_account_name":                    "Seller Account",
                "payment_service_provider_identifier":     None,
                "payment_card_primary_account_number":     None,
                "payment_card_holder_name":                None,
                "mandate_reference_identifier":            None,
                "bank_assigned_creditor_identifier":       None,
                "debited_account_identifier":              None,
                "account_address_line_1":                  None,
                "account_address_line_2":                  None,
                "account_address_line_3":                  None,
                "account_city":                            None,
                "account_post_code":                       None,
                "account_country_subdivision":             None,
                "account_country_code":                    None,
                "remittance_information":                  [],
            }
        ],
        "terms": [
            {
                "payment_terms":                "Net 14 days",
                "terms_amount":                 None,
                "terms_installment_due_date":   due_date if is_inv else None,
                "terms_payment_instructions_id": None,
            }
        ],
        "lines": lines_out,
    }

    # Delivery block
    if transaction_type in ("Exports", "eCommerce", "FTZ"):
        addr_map = {
            "Exports":   {"address_line_1": "456 Main Street", "city": "New York",
                          "country_subdivision": "NY", "country_code": "US"},
            "FTZ":       {"address_line_1": "Jebel Ali Free Zone", "city": "Dubai",
                          "country_subdivision": "DXB", "country_code": "AE"},
            "eCommerce": {"address_line_1": "Al Barsha", "city": "Dubai",
                          "country_subdivision": "DXB", "country_code": "AE"},
        }
        dlv = {"delivery_location": addr_map[transaction_type]}
        if transaction_type == "Exports":
            dlv["delivery_terms"] = {"id": "CIF", "scheme_id": "Incoterms"}
        doc["delivery"] = dlv

    # Summary / Continuous: document-level invoice period
    if transaction_type in ("Summary", "Continuous"):
        doc["invoice_period"] = {"start_date": period_start, "end_date": issue_date}

    return json.dumps(doc, indent=4, ensure_ascii=False)


# ── JSON → UBL XML converter ──────────────────────────────────────────────────

def json_to_xml(json_str: str) -> str:
    """Convert a PINT AE JSON document (new schema) to UBL 2.1 XML."""
    d = json.loads(json_str)

    type_code = str(d.get("invoice_type_code", "380"))
    # DOC_INFO uses "81" not "081"
    info      = DOC_INFO.get(type_code) or DOC_INFO.get(type_code.lstrip("0") or type_code, DOC_INFO["380"])
    is_inv    = info["is_inv"]

    root_ns  = INV_NS if is_inv else CN_NS
    root_tag = "Invoice" if is_inv else "CreditNote"
    type_tag = "InvoiceTypeCode" if is_inv else "CreditNoteTypeCode"
    line_tag = "InvoiceLine" if is_inv else "CreditNoteLine"
    qty_tag  = "InvoicedQuantity" if is_inv else "CreditedQuantity"
    curr     = d.get("invoice_currency_code", "AED")
    is_foreign = d.get("tax_currency_code") is not None

    nsmap = {None: root_ns, "cac": CAC, "cbc": CBC}
    root  = etree.Element(f"{{{root_ns}}}{root_tag}", nsmap=nsmap)

    def s(parent, local, ns=CBC, text=None, **a):
        return _sub(parent, local, ns=ns, text=text, **a)

    pc = d.get("process_control", {})
    s(root, "CustomizationID",    text=pc.get("customization_id", BILLING_URN))
    s(root, "ProfileID",          text=pc.get("profile_id", "urn:peppol:bis:billing"))
    s(root, "ProfileExecutionID", text=d.get("transaction_type_code", "00000000"))
    s(root, "ID",                 text=d.get("id", f"TEST-{_r(8)}"))
    s(root, "UUID",               text=d.get("uuid", str(uuid.uuid4())))
    s(root, "IssueDate",          text=d.get("issue_date", date.today().isoformat()))
    if d.get("issue_time"):
        s(root, "IssueTime",      text=d["issue_time"])
    if is_inv and d.get("payment_due_date"):
        s(root, "DueDate",        text=d["payment_due_date"])
    s(root, type_tag,             text=type_code)
    if d.get("invoice_note"):
        s(root, "Note",           text=d["invoice_note"])
    if is_inv and d.get("vat_point_date"):
        s(root, "TaxPointDate",   text=d["vat_point_date"])
    s(root, "DocumentCurrencyCode", text=curr)
    if is_foreign and d.get("tax_currency_code"):
        s(root, "TaxCurrencyCode",  text=d["tax_currency_code"])
    if d.get("buyer_accounting_reference"):
        s(root, "AccountingCost", text=d["buyer_accounting_reference"])
    if d.get("buyer_reference"):
        s(root, "BuyerReference", text=d["buyer_reference"])

    # InvoicePeriod (summary / continuous — stored in invoice_period object)
    if d.get("invoice_period"):
        ip = s(root, "InvoicePeriod", ns=CAC)
        if d["invoice_period"].get("start_date"):
            s(ip, "StartDate", text=d["invoice_period"]["start_date"])
        if d["invoice_period"].get("end_date"):
            s(ip, "EndDate",   text=d["invoice_period"]["end_date"])

    # OrderReference
    if d.get("purchase_order_reference") or d.get("sales_order_reference"):
        oref = s(root, "OrderReference", ns=CAC)
        s(oref, "ID", text=d.get("purchase_order_reference") or "")
        if d.get("sales_order_reference"):
            s(oref, "SalesOrderID", text=d["sales_order_reference"])

    # BillingReference (credit note preceding invoice refs)
    for ref in (d.get("preceding_invoice_references") or []):
        br  = s(root, "BillingReference", ns=CAC)
        idr = s(br, "InvoiceDocumentReference", ns=CAC)
        s(idr, "ID", text=ref.get("preceding_invoice_reference", ""))
        if ref.get("preceding_invoice_issue_date"):
            s(idr, "IssueDate", text=ref["preceding_invoice_issue_date"])

    if d.get("despatch_document_reference"):
        ddr = s(root, "DespatchDocumentReference", ns=CAC)
        s(ddr, "ID", text=d["despatch_document_reference"])

    if d.get("receipt_document_reference"):
        rdr = s(root, "ReceiptDocumentReference", ns=CAC)
        s(rdr, "ID", text=d["receipt_document_reference"])

    if d.get("originator_document_reference"):
        odr = s(root, "OriginatorDocumentReference", ns=CAC)
        s(odr, "ID", text=d["originator_document_reference"])

    if d.get("contract_document_reference"):
        cdr = s(root, "ContractDocumentReference", ns=CAC)
        s(cdr, "ID", text=d["contract_document_reference"])

    # AdditionalDocumentReference (from supporting_documents)
    for sdoc in (d.get("supporting_documents") or []):
        adr = s(root, "AdditionalDocumentReference", ns=CAC)
        s(adr, "ID", text=sdoc.get("reference", ""))
        has_att = sdoc.get("external_document_location") or sdoc.get("attached_document")
        if has_att:
            att = s(adr, "Attachment", ns=CAC)
            if sdoc.get("attached_document"):
                s(att, "EmbeddedDocumentBinaryObject",
                  mimeCode=sdoc.get("attached_document_mime_code", ""),
                  filename=sdoc.get("attached_document_filename", ""),
                  text=sdoc["attached_document"])
            if sdoc.get("external_document_location"):
                extref = s(att, "ExternalReference", ns=CAC)
                s(extref, "URI", text=sdoc["external_document_location"])

    if d.get("project_reference"):
        pr = s(root, "ProjectReference", ns=CAC)
        s(pr, "ID", text=d["project_reference"])

    # DiscrepancyResponse (credit note)
    if not is_inv and d.get("discrepancy_response_code"):
        dr = s(root, "DiscrepancyResponse", ns=CAC)
        s(dr, "ResponseCode", text=d["discrepancy_response_code"])

    # AccountingSupplierParty
    sp    = d.get("seller", {})
    sup   = s(root, "AccountingSupplierParty", ns=CAC)
    sup_p = s(sup, "Party", ns=CAC)
    s(sup_p, "EndpointID",
      schemeID=sp.get("electronic_address_scheme", "0235"),
      text=sp.get("electronic_address", ""))
    s(s(sup_p, "PartyName", ns=CAC), "Name",
      text=sp.get("trading_name") or sp.get("name", ""))
    sa = s(sup_p, "PostalAddress", ns=CAC)
    s(sa, "StreetName", text=sp.get("address_line_1", ""))
    if sp.get("address_line_2"):
        s(sa, "AdditionalStreetName", text=sp["address_line_2"])
    s(sa, "CityName",         text=sp.get("city", ""))
    if sp.get("post_code"):
        s(sa, "PostalZone",   text=sp["post_code"])
    s(sa, "CountrySubentity", text=sp.get("country_subdivision", ""))
    s(s(sa, "Country", ns=CAC), "IdentificationCode", text=sp.get("country_code", "AE"))
    if sp.get("vat_identifier"):
        stx = s(sup_p, "PartyTaxScheme", ns=CAC)
        s(stx, "CompanyID", text=sp["vat_identifier"])
        s(s(stx, "TaxScheme", ns=CAC), "ID", text=sp.get("tax_scheme", "VAT"))
    sleg = s(sup_p, "PartyLegalEntity", ns=CAC)
    s(sleg, "RegistrationName", text=sp.get("name", ""))
    sc_attrs = {
        "schemeAgencyID":   sp.get("legal_registration_identifier_type", "TL"),
        "schemeAgencyName": sp.get("authority_name", "Trade License issuing Authority"),
    }
    if sp.get("legal_registration_identifier_scheme"):
        sc_attrs["schemeID"] = sp["legal_registration_identifier_scheme"]
    s(sleg, "CompanyID", **sc_attrs,
      text=sp.get("legal_registration_identifier", ""))

    # AccountingCustomerParty
    bp    = d.get("buyer", {})
    buy   = s(root, "AccountingCustomerParty", ns=CAC)
    buy_p = s(buy, "Party", ns=CAC)
    s(buy_p, "EndpointID",
      schemeID=bp.get("electronic_address_scheme", "0235"),
      text=bp.get("electronic_address", ""))
    s(s(buy_p, "PartyName", ns=CAC), "Name",
      text=bp.get("trading_name") or bp.get("name", ""))
    ba = s(buy_p, "PostalAddress", ns=CAC)
    s(ba, "StreetName", text=bp.get("address_line_1", ""))
    if bp.get("address_line_2"):
        s(ba, "AdditionalStreetName", text=bp["address_line_2"])
    s(ba, "CityName",         text=bp.get("city", ""))
    if bp.get("post_code"):
        s(ba, "PostalZone",   text=bp["post_code"])
    s(ba, "CountrySubentity", text=bp.get("country_subdivision", ""))
    s(s(ba, "Country", ns=CAC), "IdentificationCode", text=bp.get("country_code", "AE"))
    if bp.get("vat_identifier"):
        btx = s(buy_p, "PartyTaxScheme", ns=CAC)
        s(btx, "CompanyID", text=bp["vat_identifier"])
        s(s(btx, "TaxScheme", ns=CAC), "ID", text=bp.get("tax_scheme", "VAT"))
    bleg = s(buy_p, "PartyLegalEntity", ns=CAC)
    s(bleg, "RegistrationName", text=bp.get("name", ""))
    bc_attrs = {
        "schemeAgencyID":   bp.get("legal_registration_identifier_type", "TL"),
        "schemeAgencyName": bp.get("authority_name", "Trade License issuing Authority"),
    }
    if bp.get("legal_registration_identifier_scheme"):
        bc_attrs["schemeID"] = bp["legal_registration_identifier_scheme"]
    s(bleg, "CompanyID", **bc_attrs,
      text=bp.get("legal_registration_identifier", ""))

    # BuyerCustomerParty (FTZ beneficiary stored in buyer.beneficiary_identifier)
    if bp.get("beneficiary_identifier"):
        bcp = s(root, "BuyerCustomerParty", ns=CAC)
        bpi = s(s(bcp, "Party", ns=CAC), "PartyIdentification", ns=CAC)
        s(bpi, "ID", text=bp["beneficiary_identifier"])

    # SellerSupplierParty (Disclosed Agent principal)
    if d.get("principal_identifier"):
        ssp = s(root, "SellerSupplierParty", ns=CAC)
        spi = s(s(ssp, "Party", ns=CAC), "PartyIdentification", ns=CAC)
        s(spi, "ID", text=d["principal_identifier"])

    # Delivery
    dlv_data = d.get("delivery")
    if dlv_data:
        dlv      = s(root, "Delivery", ns=CAC)
        dloc_data = dlv_data.get("delivery_location", {})
        if dloc_data:
            dloc = s(dlv, "DeliveryLocation", ns=CAC)
            dadr = s(dloc, "Address", ns=CAC)
            s(dadr, "StreetName",       text=dloc_data.get("address_line_1", ""))
            s(dadr, "CityName",         text=dloc_data.get("city", ""))
            s(dadr, "CountrySubentity", text=dloc_data.get("country_subdivision", ""))
            s(s(dadr, "Country", ns=CAC), "IdentificationCode",
              text=dloc_data.get("country_code", "AE"))
        dt_data = dlv_data.get("delivery_terms")
        if dt_data:
            dt = s(dlv, "DeliveryTerms", ns=CAC)
            s(dt, "ID",
              schemeID=dt_data.get("scheme_id", "Incoterms"),
              text=dt_data.get("id", ""))

    # PaymentMeans
    for pm_data in (d.get("payment_instructions") or []):
        pm = s(root, "PaymentMeans", ns=CAC)
        s(pm, "PaymentMeansCode", text=pm_data.get("payment_means_type_code", "30"))
        acct_id = pm_data.get("payment_account_identifier")
        card_no = pm_data.get("payment_card_primary_account_number")
        if acct_id:
            pfa = s(pm, "PayeeFinancialAccount", ns=CAC)
            s(pfa, "ID", text=acct_id)
            if pm_data.get("payment_account_name"):
                s(pfa, "Name", text=pm_data["payment_account_name"])
        if card_no:
            ca = s(pm, "CardAccount", ns=CAC)
            s(ca, "PrimaryAccountNumberID", text=card_no)
            if pm_data.get("payment_card_holder_name"):
                s(ca, "HolderName", text=pm_data["payment_card_holder_name"])

    # PaymentTerms
    for term in (d.get("terms") or []):
        if term.get("payment_terms"):
            pt = s(root, "PaymentTerms", ns=CAC)
            s(pt, "Note", text=term["payment_terms"])

    # AllowanceCharge — document level (allowances then charges)
    for alw in (d.get("allowances") or []):
        _emit_allowance_charge(root, s, alw, curr, charge=False)
    for chg in (d.get("charges") or []):
        _emit_allowance_charge(root, s, chg, curr, charge=True)

    # TaxTotal(s)
    totals = d.get("totals", {})
    total_tax_str = totals.get("invoice_total_vat_amount", "0")
    tt = s(root, "TaxTotal", ns=CAC)
    s(tt, "TaxAmount", currencyID=curr, text=total_tax_str)
    for bd in (d.get("vat_breakdowns") or []):
        sub_el = s(tt, "TaxSubtotal", ns=CAC)
        s(sub_el, "TaxableAmount", currencyID=curr,
          text=str(bd.get("taxable_amount", "0")))
        s(sub_el, "TaxAmount",     currencyID=curr,
          text=str(bd.get("tax_amount", "0")))
        tc       = s(sub_el, "TaxCategory", ns=CAC)
        cat_code = bd.get("vat_category_code", "S")
        s(tc, "ID", text=cat_code)
        if "vat_category_rate" in bd and cat_code not in ("O", "E"):
            s(tc, "Percent", text=str(bd["vat_category_rate"]))
        if bd.get("vat_exemption_reason_code"):
            s(tc, "TaxExemptionReasonCode", text=bd["vat_exemption_reason_code"])
        s(s(tc, "TaxScheme", ns=CAC), "ID", text=bd.get("tax_scheme_code", "VAT"))

    # Second TaxTotal in accounting currency (foreign currency invoices)
    if is_foreign and d.get("tax_currency_code"):
        aed_tax = totals.get("invoice_total_vat_amount_in_accounting_currency", total_tax_str)
        tt2 = s(root, "TaxTotal", ns=CAC)
        s(tt2, "TaxAmount", currencyID=d["tax_currency_code"], text=str(aed_tax))

    # LegalMonetaryTotal
    lmt = s(root, "LegalMonetaryTotal", ns=CAC)
    s(lmt, "LineExtensionAmount", currencyID=curr,
      text=str(totals.get("sum_of_invoice_line_net_amount", "0")))
    s(lmt, "TaxExclusiveAmount",  currencyID=curr,
      text=str(totals.get("invoice_total_amount_without_vat", "0")))
    s(lmt, "TaxInclusiveAmount",  currencyID=curr,
      text=str(totals.get("invoice_total_amount_with_vat", "0")))
    _alw = str(totals.get("sum_of_allowances_on_document_level", "0.00"))
    if Decimal(_alw) != 0:
        s(lmt, "AllowanceTotalAmount", currencyID=curr, text=_alw)
    _chg = str(totals.get("sum_of_charges_on_document_level", "0.00"))
    if Decimal(_chg) != 0:
        s(lmt, "ChargeTotalAmount", currencyID=curr, text=_chg)
    _paid = str(totals.get("paid_amount", "0.00"))
    if Decimal(_paid) != 0:
        s(lmt, "PrepaidAmount", currencyID=curr, text=_paid)
    _round = str(totals.get("rounding_amount", "0.00"))
    if Decimal(_round) != 0:
        s(lmt, "PayableRoundingAmount", currencyID=curr, text=_round)
    s(lmt, "PayableAmount", currencyID=curr,
      text=str(totals.get("amount_due_for_payment", "0")))

    # Lines
    for line in d.get("lines", []):
        line_el = s(root, line_tag, ns=CAC)
        s(line_el, "ID", text=str(line.get("line_id", "1")))
        if line.get("note"):
            s(line_el, "Note", text=line["note"])
        s(line_el, qty_tag,
          unitCode=line.get("invoiced_quantity_unit_of_measure_code", "C62"),
          text=str(line.get("invoiced_quantity", "1")))
        s(line_el, "LineExtensionAmount",
          currencyID=curr,
          text=str(line.get("line_net_amount", "0")))
        if line.get("buyer_accounting_reference"):
            s(line_el, "AccountingCost", text=line["buyer_accounting_reference"])
        if line.get("purchase_order_line_reference"):
            olr = s(line_el, "OrderLineReference", ns=CAC)
            s(olr, "LineID", text=str(line["purchase_order_line_reference"]))
        if line.get("line_period_start_date") or line.get("line_period_end_date"):
            lp = s(line_el, "InvoicePeriod", ns=CAC)
            if line.get("line_period_start_date"):
                s(lp, "StartDate", text=line["line_period_start_date"])
            if line.get("line_period_end_date"):
                s(lp, "EndDate", text=line["line_period_end_date"])

        # Line-level AllowanceCharge
        for alw in (line.get("allowances") or []):
            _emit_allowance_charge(line_el, s, alw, curr, charge=False)
        for chg in (line.get("charges") or []):
            _emit_allowance_charge(line_el, s, chg, curr, charge=True)

        # Item
        item_el = s(line_el, "Item", ns=CAC)
        if line.get("item_description"):
            s(item_el, "Description", text=line["item_description"])
        s(item_el, "Name", text=line.get("item_name", ""))
        if line.get("item_buyers_identifier"):
            biid = s(item_el, "BuyersItemIdentification", ns=CAC)
            s(biid, "ID", text=line["item_buyers_identifier"])
        if line.get("item_sellers_identifier"):
            siid = s(item_el, "SellersItemIdentification", ns=CAC)
            s(siid, "ID", text=line["item_sellers_identifier"])
        if line.get("item_standard_identifier"):
            sii = s(item_el, "StandardItemIdentification", ns=CAC)
            s(sii, "ID",
              schemeID=line.get("item_standard_identifier_scheme", "0160"),
              text=line["item_standard_identifier"])
        if line.get("item_country_of_origin"):
            oc = s(item_el, "OriginCountry", ns=CAC)
            s(oc, "IdentificationCode", text=line["item_country_of_origin"])
        if line.get("type_of_goods_or_services"):
            cc = s(item_el, "CommodityClassification", ns=CAC)
            s(cc, "NatureCode", text=line["type_of_goods_or_services"])

        vat_info_list = line.get("vat_info") or []
        vat_info  = vat_info_list[0] if vat_info_list else {}
        cat_code  = vat_info.get("vat_category_code", "S")
        ctc = s(item_el, "ClassifiedTaxCategory", ns=CAC)
        s(ctc, "ID", text=cat_code)
        vat_rate_val = vat_info.get("vat_rate")
        if vat_rate_val is not None and cat_code not in ("O", "E"):
            s(ctc, "Percent", text=str(vat_rate_val))
        if vat_info.get("vat_exemption_reason_code"):
            s(ctc, "TaxExemptionReasonCode", text=vat_info["vat_exemption_reason_code"])
        s(s(ctc, "TaxScheme", ns=CAC), "ID", text=vat_info.get("tax_scheme", "VAT"))

        # Price
        price = s(line_el, "Price", ns=CAC)
        s(price, "PriceAmount", currencyID=curr,
          text=str(line.get("item_net_price", "0")))
        s(price, "BaseQuantity",
          unitCode=line.get("item_price_base_quantity_unit_of_measure_code", "C62"),
          text=str(line.get("item_price_base_quantity", "1")))
        pac = s(price, "AllowanceCharge", ns=CAC)
        s(pac, "ChargeIndicator", text="false")
        s(pac, "Amount", currencyID=curr,
          text=str(line.get("item_price_discount", "0.00")))
        s(pac, "BaseAmount", currencyID=curr,
          text=str(line.get("item_gross_price") or line.get("item_net_price", "0")))

        # ItemPriceExtension
        ipe = s(line_el, "ItemPriceExtension", ns=CAC)
        s(ipe, "Amount", currencyID=curr, text=str(line.get("line_net_amount", "0")))
        vat_line_amt = line.get("vat_line_amount_in_aed")
        if vat_line_amt is not None:
            s(s(ipe, "TaxTotal", ns=CAC), "TaxAmount",
              currencyID=curr,
              text=_fmt(Decimal(str(vat_line_amt)).quantize(Decimal("0.01"))))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                          pretty_print=True).decode()


def _emit_allowance_charge(parent, s_fn, item: dict, curr: str, charge: bool):
    ac = s_fn(parent, "AllowanceCharge", ns=CAC)
    s_fn(ac, "ChargeIndicator", text="true" if charge else "false")
    if item.get("reason_code"):
        s_fn(ac, "AllowanceChargeReasonCode", text=str(item["reason_code"]))
    if item.get("reason"):
        s_fn(ac, "AllowanceChargeReason", text=item["reason"])
    if item.get("percentage"):
        s_fn(ac, "MultiplierFactorNumeric", text=str(item["percentage"]))
    s_fn(ac, "Amount", currencyID=curr, text=str(item.get("amount", "0")))
    if item.get("base_amount"):
        s_fn(ac, "BaseAmount", currencyID=curr, text=str(item["base_amount"]))
    cat = item.get("vat_category_code")
    if cat:
        tc = s_fn(ac, "TaxCategory", ns=CAC)
        s_fn(tc, "ID", text=cat)
        if item.get("vat_rate") and cat not in ("O", "E"):
            s_fn(tc, "Percent", text=str(item["vat_rate"]))
        s_fn(s_fn(tc, "TaxScheme", ns=CAC), "ID", text=item.get("tax_scheme_code", "VAT"))
