#!/usr/bin/env python3
"""PINT AE UBL XML Generator — produces schematron-compliant test invoices."""

import uuid
import random
import string
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from lxml import etree

INV_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CN_NS  = "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
CAC    = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC    = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

BILLING_URN      = "urn:peppol:pint:billing-1@ae-1"
SELF_BILLING_URN = "urn:peppol:pint:selfbilling-1@ae-1"

DOC_INFO = {
    "380": dict(is_inv=True,  is_sb=False, line_tag="InvoiceLine",    qty_tag="InvoicedQuantity",  type_tag="InvoiceTypeCode",    label="Tax Invoice"),
    "381": dict(is_inv=False, is_sb=False, line_tag="CreditNoteLine", qty_tag="CreditedQuantity",  type_tag="CreditNoteTypeCode", label="Tax Credit Note"),
    "480": dict(is_inv=True,  is_sb=False, line_tag="InvoiceLine",    qty_tag="InvoicedQuantity",  type_tag="InvoiceTypeCode",    label="Commercial Invoice"),
    "81":  dict(is_inv=False, is_sb=False, line_tag="CreditNoteLine", qty_tag="CreditedQuantity",  type_tag="CreditNoteTypeCode", label="Commercial Credit Note"),
    "389": dict(is_inv=True,  is_sb=True,  line_tag="InvoiceLine",    qty_tag="InvoicedQuantity",  type_tag="InvoiceTypeCode",    label="Self-Billing Invoice"),
    "261": dict(is_inv=False, is_sb=True,  line_tag="CreditNoteLine", qty_tag="CreditedQuantity",  type_tag="CreditNoteTypeCode", label="Self-Billing Credit Note"),
}

# ProfileExecutionID bits: FTZ Deemed Margin Summary Continuous Agent eCommerce Exports
TRN_FLAGS = {
    "Standard":   "00000000",
    "FTZ":        "10000000",
    "Deemed":     "01000000",
    "Margin":     "00100000",
    "Summary":    "00010000",
    "Continuous": "00001000",
    "Agent":      "00000100",
    "eCommerce":  "00000010",
    "Exports":    "00000001",
}

FX_RATES = {
    "USD": Decimal("3.67285"),
    "EUR": Decimal("4.01000"),
    "GBP": Decimal("4.65000"),
}

# (has_pct, pct, has_ipe_tax, line_tax_is_zero)
# E  → no Percent, no IPE TaxTotal (ibr-163-ae, aligned-ibrp-e-05)
# O  → no Percent on lines or breakdown (aligned-ibrp-o-05/11); TaxAmount=0
# AE → Percent=5 (ibr-174-ae/ibr-111-ae pattern), TaxAmount=0 in IPE (buyer pays)
# N  → Percent=5 (ibr-111-ae: must not be zero), TaxAmount=0 in IPE (margin scheme)
VAT_CFG = {
    "S":  dict(has_pct=True,  pct=Decimal("5.00"), has_ipe_tax=True,  line_tax_is_zero=False),
    "Z":  dict(has_pct=True,  pct=Decimal("0.00"), has_ipe_tax=True,  line_tax_is_zero=True),
    "E":  dict(has_pct=False, pct=Decimal("0.00"), has_ipe_tax=False, line_tax_is_zero=True),
    "O":  dict(has_pct=False, pct=Decimal("0.00"), has_ipe_tax=True,  line_tax_is_zero=True),
    "AE": dict(has_pct=True,  pct=Decimal("5.00"), has_ipe_tax=True,  line_tax_is_zero=True),
    "N":  dict(has_pct=True,  pct=Decimal("5.00"), has_ipe_tax=True,  line_tax_is_zero=True),
}

EMIRATE_CODES = ["DXB", "AUH", "SHJ"]


def _fmt(d: Decimal, places: int = 2) -> str:
    q = Decimal(10) ** -places
    return str(d.quantize(q, rounding=ROUND_HALF_UP))


def _r(n: int) -> str:
    return "".join(random.choices(string.digits, k=n))


def _trn() -> str:
    """Generate a valid-format UAE TRN: 15 digits, starts with 1, ends with 03."""
    return f"1{_r(12)}03"


def _sub(parent, local: str, ns: str = CBC, text=None, **attrib) -> etree._Element:
    el = etree.SubElement(parent, f"{{{ns}}}{local}", **attrib)
    if text is not None:
        el.text = str(text)
    return el


def generate(
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
    item_type: str = "S",            # G=Goods, S=Services, B=Both — drives AE NatureCode
    ftz_beneficiary_id: str = "",    # ibr-007-ae: required for FTZ transaction type
    agent_principal_id: str = "",    # ibr-137-ae: Principal VAT ID for Disclosed Agent (BTAE-14); must differ from supplier_vat
) -> str:

    info       = DOC_INFO[doc_type]
    is_inv     = info["is_inv"]
    is_sb      = info["is_sb"]
    is_cn      = not is_inv
    is_export  = transaction_type == "Exports"
    is_margin  = transaction_type == "Margin"
    is_foreign = currency != "AED"

    # ── Defaults ────────────────────────────────────────────────────────────
    # VAT numbers: 15 digits, starts with 1, ends with 03 (ibr-132-ae)
    supplier_endpoint_id  = supplier_endpoint_id  or _trn()
    buyer_endpoint_id     = buyer_endpoint_id     or _trn()
    ftz_beneficiary_id    = ftz_beneficiary_id    or _trn()
    # ibr-176-ae: agent principal ID must differ from supplier_vat
    if not agent_principal_id:
        agent_principal_id = f"1{_r(12)}03"
        while agent_principal_id == supplier_vat:
            agent_principal_id = f"1{_r(12)}03"
    supplier_vat          = supplier_vat          or _trn()
    buyer_vat             = buyer_vat             or _trn()
    supplier_tl           = supplier_tl           or _trn()
    buyer_tl              = buyer_tl             or _trn()
    supplier_name         = supplier_name         or "Supplier Trade Name"
    buyer_name            = buyer_name            or "Buyer Trade Name"

    today        = date.today()
    issue_date   = today.isoformat()
    # ibr-141-ae: TaxPointDate MUST be before IssueDate → use yesterday
    tax_point    = (today - timedelta(days=1)).isoformat()
    due_date     = (today + timedelta(days=30)).isoformat()
    prior_date   = (today - timedelta(days=7)).isoformat()
    period_start = (today - timedelta(days=30)).isoformat()
    flags        = TRN_FLAGS.get(transaction_type, "00000000")
    curr         = currency

    # ── Pre-compute line financials ─────────────────────────────────────────
    LINE_AMT = Decimal("1000.00")
    UNIT_PRC = Decimal("100.00")
    UNIT_QTY = 10
    UNIT_CODE = "C62"    # ibr-cl-23: must be valid UN/ECE Rec 20 code

    lines = []
    for i, cat in enumerate(vat_categories, 1):
        cfg = VAT_CFG[cat]
        # Compute line VAT amount
        if cfg["line_tax_is_zero"] or not cfg["has_pct"]:
            line_tax = Decimal("0.00")
        else:
            line_tax = (LINE_AMT * cfg["pct"] / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
        lines.append({
            "idx": i, "cat": cat,
            "has_pct": cfg["has_pct"], "pct": cfg["pct"],
            "has_ipe_tax": cfg["has_ipe_tax"],
            "line_ext": LINE_AMT, "line_tax": line_tax,
        })

    # Aggregate breakdown subtotals per category
    subtotals = {}
    for l in lines:
        cat = l["cat"]
        if cat not in subtotals:
            subtotals[cat] = {
                "taxable": Decimal("0"), "tax": Decimal("0"),
                "has_pct": l["has_pct"], "pct": l["pct"],
            }
        subtotals[cat]["taxable"] += l["line_ext"]
        subtotals[cat]["tax"]     += l["line_tax"]

    total_line_ext = sum(l["line_ext"] for l in lines)
    total_tax      = sum(v["tax"] for v in subtotals.values())
    tax_excl       = total_line_ext
    tax_incl       = tax_excl + total_tax

    # ── Build root ──────────────────────────────────────────────────────────
    root_ns  = INV_NS if is_inv else CN_NS
    root_tag = "Invoice" if is_inv else "CreditNote"
    nsmap    = {None: root_ns, "cac": CAC, "cbc": CBC}
    root     = etree.Element(f"{{{root_ns}}}{root_tag}", nsmap=nsmap)

    # ── Document header ─────────────────────────────────────────────────────
    _sub(root, "CustomizationID",    text=SELF_BILLING_URN if is_sb else BILLING_URN)
    _sub(root, "ProfileID",          text="urn:peppol:bis:selfbilling" if is_sb else "urn:peppol:bis:billing")
    _sub(root, "ProfileExecutionID", text=flags)
    _sub(root, "ID",                 text=f"TEST-{_r(8)}")
    _sub(root, "UUID",               text=str(uuid.uuid4()))
    _sub(root, "IssueDate",          text=issue_date)
    _sub(root, "IssueTime",          text="09:00:00+04:00")
    if is_inv:
        _sub(root, "DueDate",        text=due_date)
    _sub(root, info["type_tag"],     text=doc_type)
    _sub(root, "Note",               text=info["label"])
    # ibr-141-ae: TaxPointDate must be BEFORE IssueDate; omit for Margin (N)
    if is_inv and not is_margin:
        _sub(root, "TaxPointDate",   text=tax_point)
    _sub(root, "DocumentCurrencyCode", text=curr)
    if is_foreign:
        _sub(root, "TaxCurrencyCode",  text="AED")
    _sub(root, "BuyerReference",     text=f"PO-{_r(6)}")

    if transaction_type in ("Summary", "Continuous"):
        ip = _sub(root, "InvoicePeriod", ns=CAC)
        _sub(ip, "StartDate", text=period_start)
        _sub(ip, "EndDate",   text=issue_date)

    if is_cn:
        dr = _sub(root, "DiscrepancyResponse", ns=CAC)
        _sub(dr, "ResponseCode", text="DL8.61.1.E")

    oref = _sub(root, "OrderReference", ns=CAC)
    _sub(oref, "ID", text=f"PO-{_r(6)}")

    if is_cn:
        br  = _sub(root, "BillingReference", ns=CAC)
        idr = _sub(br, "InvoiceDocumentReference", ns=CAC)
        _sub(idr, "ID",        text=f"INV-{_r(8)}")
        _sub(idr, "IssueDate", text=prior_date)

    # ibr-175-ae: for non-AED invoices include AED total-incl-vat reference
    if is_foreign:
        rate_val = FX_RATES.get(curr, Decimal("3.67285"))
        aed_total = (tax_incl * rate_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        adr = _sub(root, "AdditionalDocumentReference", ns=CAC)
        _sub(adr, "ID",                  text="AED")
        _sub(adr, "DocumentTypeCode",    text="aedtotal-incl-vat")
        _sub(adr, "DocumentDescription", text=f"AED {_fmt(aed_total)}")

    # ── Supplier ────────────────────────────────────────────────────────────
    sup   = _sub(root, "AccountingSupplierParty", ns=CAC)
    sup_p = _sub(sup, "Party", ns=CAC)
    _sub(sup_p, "EndpointID", schemeID=supplier_endpoint_scheme, text=supplier_endpoint_id)
    _sub(_sub(sup_p, "PartyName", ns=CAC), "Name", text=supplier_name)
    sup_addr = _sub(sup_p, "PostalAddress", ns=CAC)
    _sub(sup_addr, "StreetName",       text="Sheikh Zayed Road")
    _sub(sup_addr, "CityName",         text="Dubai")
    _sub(sup_addr, "CountrySubentity", text=random.choice(EMIRATE_CODES))
    _sub(_sub(sup_addr, "Country", ns=CAC), "IdentificationCode", text="AE")
    sup_tax = _sub(sup_p, "PartyTaxScheme", ns=CAC)
    _sub(sup_tax, "CompanyID", text=supplier_vat)
    _sub(_sub(sup_tax, "TaxScheme", ns=CAC), "ID", text="VAT")
    sup_leg = _sub(sup_p, "PartyLegalEntity", ns=CAC)
    _sub(sup_leg, "RegistrationName", text=f"{supplier_name} Legal")
    _sub(sup_leg, "CompanyID",
         schemeAgencyID="TL",
         schemeAgencyName="Trade License issuing Authority",
         text=supplier_tl)

    # ── Buyer ────────────────────────────────────────────────────────────────
    buy   = _sub(root, "AccountingCustomerParty", ns=CAC)
    buy_p = _sub(buy, "Party", ns=CAC)
    eff_buy_scheme = buyer_endpoint_scheme
    _sub(buy_p, "EndpointID", schemeID=eff_buy_scheme, text=buyer_endpoint_id)
    _sub(_sub(buy_p, "PartyName", ns=CAC), "Name", text=buyer_name)
    buy_addr = _sub(buy_p, "PostalAddress", ns=CAC)

    if is_export:
        _sub(buy_addr, "StreetName",       text="123 Export Street")
        _sub(buy_addr, "CityName",         text="London")
        _sub(buy_addr, "CountrySubentity", text="ENG")
        _sub(_sub(buy_addr, "Country", ns=CAC), "IdentificationCode", text="GB")
        buy_leg = _sub(buy_p, "PartyLegalEntity", ns=CAC)
        _sub(buy_leg, "RegistrationName", text=buyer_name)
        # ibr-180-ae: when buyer endpoint schemeID=0235, CompanyID must have schemeAgencyName
        _sub(buy_leg, "CompanyID",
             schemeAgencyID="TL",
             schemeAgencyName="Trade License issuing Authority",
             text=buyer_tl)
    else:
        _sub(buy_addr, "StreetName",       text="Al Khalidiyah Street")
        _sub(buy_addr, "CityName",         text="Abu Dhabi")
        _sub(buy_addr, "CountrySubentity", text="AUH")
        _sub(_sub(buy_addr, "Country", ns=CAC), "IdentificationCode", text="AE")
        buy_tax = _sub(buy_p, "PartyTaxScheme", ns=CAC)
        _sub(buy_tax, "CompanyID", text=buyer_vat)
        _sub(_sub(buy_tax, "TaxScheme", ns=CAC), "ID", text="VAT")
        buy_leg = _sub(buy_p, "PartyLegalEntity", ns=CAC)
        _sub(buy_leg, "RegistrationName", text=buyer_name)
        _sub(buy_leg, "CompanyID",
             schemeAgencyID="TL",
             schemeAgencyName="Trade License issuing Authority",
             text=buyer_tl)

    # ibr-007-ae: FTZ requires BuyerCustomerParty/Party/PartyIdentification/ID (BTAE-01)
    if transaction_type == "FTZ":
        bcp    = _sub(root, "BuyerCustomerParty", ns=CAC)
        bcp_p  = _sub(bcp, "Party", ns=CAC)
        bcp_pi = _sub(bcp_p, "PartyIdentification", ns=CAC)
        _sub(bcp_pi, "ID", text=ftz_beneficiary_id)

    # ibr-137-ae: Agent billing requires SellerSupplierParty/Party/PartyIdentification/ID (BTAE-14)
    if transaction_type == "Agent":
        ssp    = _sub(root, "SellerSupplierParty", ns=CAC)
        ssp_p  = _sub(ssp, "Party", ns=CAC)
        ssp_pi = _sub(ssp_p, "PartyIdentification", ns=CAC)
        _sub(ssp_pi, "ID", text=agent_principal_id)

    # ── Delivery ────────────────────────────────────────────────────────────
    if transaction_type in ("Exports", "eCommerce", "FTZ"):
        dlv  = _sub(root, "Delivery", ns=CAC)
        dloc = _sub(dlv, "DeliveryLocation", ns=CAC)
        dadr = _sub(dloc, "Address", ns=CAC)
        if transaction_type == "Exports":
            _sub(dadr, "StreetName",       text="456 Main Street")
            _sub(dadr, "CityName",         text="New York")
            _sub(dadr, "CountrySubentity", text="NY")
            _sub(_sub(dadr, "Country", ns=CAC), "IdentificationCode", text="US")
            dt = _sub(dlv, "DeliveryTerms", ns=CAC)
            _sub(dt, "ID", schemeID="Incoterms", text="CIF")
        elif transaction_type == "FTZ":
            _sub(dadr, "StreetName",       text="Jebel Ali Free Zone")
            _sub(dadr, "CityName",         text="Dubai")
            _sub(dadr, "CountrySubentity", text="DXB")
            _sub(_sub(dadr, "Country", ns=CAC), "IdentificationCode", text="AE")
        else:  # eCommerce
            _sub(dadr, "StreetName",       text="Al Barsha")
            _sub(dadr, "CityName",         text="Dubai")
            _sub(dadr, "CountrySubentity", text="DXB")
            _sub(_sub(dadr, "Country", ns=CAC), "IdentificationCode", text="AE")

    # ── PaymentMeans ────────────────────────────────────────────────────────
    if is_inv and transaction_type != "Deemed":
        pm = _sub(root, "PaymentMeans", ns=CAC)
        _sub(pm, "PaymentMeansCode", text="30")
        pfa = _sub(pm, "PayeeFinancialAccount", ns=CAC)
        _sub(pfa, "ID", text="AE070331234567890123456")

    pt = _sub(root, "PaymentTerms", ns=CAC)
    _sub(pt, "Note", text="Net 30 days")

    # ── TaxExchangeRate ──────────────────────────────────────────────────────
    if is_foreign:
        rate_val = FX_RATES.get(curr, Decimal("3.67285"))
        ter = _sub(root, "TaxExchangeRate", ns=CAC)
        _sub(ter, "SourceCurrencyCode", text=curr)
        _sub(ter, "TargetCurrencyCode", text="AED")
        _sub(ter, "CalculationRate",    text=_fmt(rate_val, 5))

    # ── TaxTotal ─────────────────────────────────────────────────────────────
    tt = _sub(root, "TaxTotal", ns=CAC)
    _sub(tt, "TaxAmount", currencyID=curr, text=_fmt(total_tax))

    for cat, st in subtotals.items():
        sub_el = _sub(tt, "TaxSubtotal", ns=CAC)
        _sub(sub_el, "TaxableAmount", currencyID=curr, text=_fmt(st["taxable"]))
        _sub(sub_el, "TaxAmount",     currencyID=curr, text=_fmt(st["tax"]))
        tc = _sub(sub_el, "TaxCategory", ns=CAC)
        _sub(tc, "ID", text=cat)
        # O and E: no Percent in breakdown (aligned-ibrp-o-11-ae, ibr-121-ae)
        if st["has_pct"] and cat not in ("O", "E"):
            _sub(tc, "Percent", text=_fmt(st["pct"]))
        if cat == "E":
            _sub(tc, "TaxExemptionReasonCode", text="VATEX-AE-IBRZ")
        _sub(_sub(tc, "TaxScheme", ns=CAC), "ID", text="VAT")

    # Second TaxTotal in AED for multi-currency docs
    if is_foreign:
        rate_val = FX_RATES.get(curr, Decimal("3.67285"))
        tax_aed  = (total_tax * rate_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tt2 = _sub(root, "TaxTotal", ns=CAC)
        _sub(tt2, "TaxAmount", currencyID="AED", text=_fmt(tax_aed))

    # ── LegalMonetaryTotal ───────────────────────────────────────────────────
    lmt = _sub(root, "LegalMonetaryTotal", ns=CAC)
    _sub(lmt, "LineExtensionAmount", currencyID=curr, text=_fmt(total_line_ext))
    _sub(lmt, "TaxExclusiveAmount",  currencyID=curr, text=_fmt(tax_excl))
    _sub(lmt, "TaxInclusiveAmount",  currencyID=curr, text=_fmt(tax_incl))
    _sub(lmt, "PayableAmount",       currencyID=curr, text=_fmt(tax_incl))

    # ── Lines (must come after LegalMonetaryTotal per UBL schema) ────────────
    for l in lines:
        cat = l["cat"]
        cfg = VAT_CFG[cat]
        line_el = _sub(root, info["line_tag"], ns=CAC)
        _sub(line_el, "ID",                 text=str(l["idx"]))
        _sub(line_el, info["qty_tag"],       unitCode=UNIT_CODE, text=str(UNIT_QTY))
        _sub(line_el, "LineExtensionAmount", currencyID=curr, text=_fmt(l["line_ext"]))

        item = _sub(line_el, "Item", ns=CAC)
        _sub(item, "Description", text=f"{cat}-rated supply — generated test instance")
        _sub(item, "Name",        text=f"Test Item {l['idx']} [{cat}]")

        # ibr-174-ae: AE needs StandardItemIdentification/ID[@schemeID="0160"] (IBT-157)
        if cat == "AE":
            sii = _sub(item, "StandardItemIdentification", ns=CAC)
            _sub(sii, "ID", schemeID="0160", text=f"RC-{_r(8)}")

        # ibr-166-ae: AE needs CommodityClassification/NatureCode (BTAE-09 type of goods/services)
        if cat == "AE":
            cc = _sub(item, "CommodityClassification", ns=CAC)
            # NatureCode = goods/services type; map item_type to UAE regulation code
            nature_map = {"G": "DL8.48.3.1", "S": "DL8.48.3.2", "B": "DL8.48.3.3"}
            _sub(cc, "NatureCode", text=nature_map.get(item_type, "DL8.48.3.2"))

        ctc = _sub(item, "ClassifiedTaxCategory", ns=CAC)
        _sub(ctc, "ID", text=cat)
        # O: no Percent on line (aligned-ibrp-o-05); E: no Percent (aligned-ibrp-e-05)
        if cfg["has_pct"] and cat not in ("O", "E"):
            _sub(ctc, "Percent", text=_fmt(cfg["pct"]))
        # N (Margin): PerUnitAmount required (BTAE-specific)
        if cat == "N":
            _sub(ctc, "PerUnitAmount", currencyID=curr, text=_fmt(UNIT_PRC))
        # ibr-167-ae: E lines need TaxExemptionReasonCode in ClassifiedTaxCategory
        if cat == "E":
            _sub(ctc, "TaxExemptionReasonCode", text="VATEX-AE-IBRZ")
        _sub(_sub(ctc, "TaxScheme", ns=CAC), "ID", text="VAT")

        price = _sub(line_el, "Price", ns=CAC)
        _sub(price, "PriceAmount",  currencyID=curr, text=_fmt(UNIT_PRC))
        _sub(price, "BaseQuantity", unitCode=UNIT_CODE, text="1")
        pac = _sub(price, "AllowanceCharge", ns=CAC)
        _sub(pac, "ChargeIndicator", text="false")
        _sub(pac, "Amount",          currencyID=curr, text="0.00")
        _sub(pac, "BaseAmount",      currencyID=curr, text=_fmt(UNIT_PRC))

        # ItemPriceExtension — BTAE-10 (Amount) and BTAE-08 (TaxAmount)
        # E: no TaxTotal in IPE (ibr-163-ae)
        ipe = _sub(line_el, "ItemPriceExtension", ns=CAC)
        _sub(ipe, "Amount", currencyID=curr, text=_fmt(l["line_ext"]))
        if cfg["has_ipe_tax"]:
            _sub(_sub(ipe, "TaxTotal", ns=CAC), "TaxAmount",
                 currencyID=curr, text=_fmt(l["line_tax"]))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                          pretty_print=True).decode()
