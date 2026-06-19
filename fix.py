#!/usr/bin/env python3
"""
PINT AE (UAE) UBL Invoice/CreditNote Auto-Fixer
Validates, applies targeted fixes per rule ID, then saves <name>_valid.xml
"""

import sys
import uuid
import argparse
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from dataclasses import dataclass, field

try:
    from lxml import etree
except ImportError:
    print("ERROR: lxml not installed. Run: pip install lxml", file=sys.stderr)
    sys.exit(1)

from validate import validate, ValidationIssue, ValidationResult, BILLING_URN, SELF_BILLING_URN

# ── Namespace constants ──────────────────────────────────────────────────────
CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS = {
    "cbc": CBC,
    "cac": CAC,
    "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cn": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
}
CBC_ = f"{{{CBC}}}"
CAC_ = f"{{{CAC}}}"

MAX_ROUNDS = 6


# ── Helpers ──────────────────────────────────────────────────────────────────

def _el(local: str, text: str = None, attrib: dict = None, ns: str = CBC) -> etree._Element:
    el = etree.Element(f"{{{ns}}}{local}", attrib=attrib or {})
    if text is not None:
        el.text = text
    return el

def _cac(local: str) -> etree._Element:
    return etree.Element(f"{{{CAC}}}{local}")

def _find(root, xpath):
    return root.xpath(xpath, namespaces=NS)

def _find1(root, xpath):
    r = _find(root, xpath)
    return r[0] if r else None

def _dec(val) -> Decimal:
    try:
        return Decimal(str(val or "0").strip())
    except InvalidOperation:
        return Decimal("0")

def _fmt(d: Decimal, places: int = 2) -> str:
    q = Decimal(10) ** -places
    return str(d.quantize(q, rounding=ROUND_HALF_UP))

def _currency(root) -> str:
    el = _find1(root, "/*/cbc:DocumentCurrencyCode")
    return el.text.strip() if el is not None else "AED"


# ── Fix functions ─────────────────────────────────────────────────────────────
# Each returns True if it changed anything.

def fix_customization_id(root, _issues):
    """aligned-ibrp-001-ae: CustomizationID must be a valid PINT AE Billing or Self-Billing URN."""
    el = _find1(root, "/*/cbc:CustomizationID")
    text = (el.text or "").strip() if el is not None else ""
    if text.startswith(BILLING_URN) or text.startswith(SELF_BILLING_URN):
        return False  # already valid — do not touch
    if el is None:
        root.insert(0, _el("CustomizationID", BILLING_URN))
        return True
    el.text = BILLING_URN
    return True


def fix_profile_id(root, _issues):
    """aligned-ibrp-002-ae: ProfileID must be urn:peppol:bis:billing"""
    el = _find1(root, "/*/cbc:ProfileID")
    if el is not None and el.text not in ("urn:peppol:bis:billing", "urn:peppol:bis:selfbilling"):
        el.text = "urn:peppol:bis:billing"
        return True
    return False


def fix_profile_execution_id(root, _issues):
    """ibr-154-ae: ProfileExecutionID must be 8-char binary string (0/1 only)"""
    import re
    el = _find1(root, "/*/cbc:ProfileExecutionID")
    if el is None:
        new = _el("ProfileExecutionID", "00000000")
        pid = _find1(root, "/*/cbc:ProfileID")
        if pid is not None:
            pid.addnext(new)
        else:
            root.insert(0, new)
        return True
    text = (el.text or "").strip()
    if not re.match(r"^[01]{8}$", text):
        cleaned = re.sub(r"[^01]", "0", text)
        el.text = (cleaned + "00000000")[:8]
        return True
    return False


def fix_tax_currency_code(root, _issues):
    """ibr-140-ae: TaxCurrencyCode must be AED"""
    el = _find1(root, "/*/cbc:TaxCurrencyCode")
    if el is not None and el.text != "AED":
        el.text = "AED"
        return True
    return False


def fix_uuid(root, _issues):
    """ibr-193-ae: UUID must be present"""
    if _find1(root, "/*/cbc:UUID") is None:
        new = _el("UUID", str(uuid.uuid4()))
        id_el = _find1(root, "/*/cbc:ID")
        if id_el is not None:
            id_el.addnext(new)
        else:
            root.append(new)
        return True
    return False


def fix_remove_tax_point_date_creditnote(root, _issues):
    """ibr-124-ae: TaxPointDate must not be in credit notes"""
    cn_code = _find1(root, "/*/cbc:CreditNoteTypeCode")
    if cn_code is None:
        return False
    changed = False
    for el in _find(root, "/*/cbc:TaxPointDate"):
        el.getparent().remove(el)
        changed = True
    return changed


def fix_standard_vat_rate(root, _issues):
    """ibr-190-ae / aligned-ibrp-s-05/06/07: Standard rated VAT % must be 5.00 and > 0"""
    changed = False
    for el in (_find(root, "//cac:TaxCategory[cbc:ID='S']/cbc:Percent") +
               _find(root, "//cac:ClassifiedTaxCategory[cbc:ID='S']/cbc:Percent")):
        if el.text != "5.00":
            el.text = "5.00"
            changed = True
    return changed


def fix_exempt_line_percent(root, _issues):
    """aligned-ibrp-e-05: Exempt line item Percent shall not be present"""
    changed = False
    for cat in _find(root, "//cac:ClassifiedTaxCategory[cbc:ID='E']"):
        for pct in cat.findall(f"{CBC_}Percent"):
            cat.remove(pct)
            changed = True
    return changed


def fix_exempt_allowance_charge_percent(root, _issues):
    """aligned-ibrp-e-06/07: Exempt allowance/charge VAT rate must be 0"""
    changed = False
    for el in _find(root, "//cac:AllowanceCharge/cac:TaxCategory[cbc:ID='E']/cbc:Percent"):
        if el.text != "0":
            el.text = "0"
            changed = True
    return changed


def fix_zero_rated_percent(root, _issues):
    """aligned-ibrp-z-05/06/07, ibr-120-ae: Zero rated VAT % must be 0"""
    changed = False
    for el in (_find(root, "//cac:TaxCategory[cbc:ID='Z']/cbc:Percent") +
               _find(root, "//cac:ClassifiedTaxCategory[cbc:ID='Z']/cbc:Percent")):
        if el.text != "0":
            el.text = "0"
            changed = True
    return changed


def fix_exempt_breakdown_percent(root, _issues):
    """ibr-121-ae: Exempt VAT breakdown Percent shall not be present"""
    changed = False
    for sub in _find(root, "//cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory[cbc:ID='E']"):
        for pct in sub.findall(f"{CBC_}Percent"):
            sub.remove(pct)
            changed = True
    return changed


def fix_exempt_breakdown_tax_amount(root, _issues):
    """aligned-ibrp-e-09: Exempt VAT breakdown TaxAmount must be 0"""
    changed = False
    for sub in _find(root, "//cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cbc:ID='E']"):
        el = sub.find(f"{CBC_}TaxAmount")
        if el is not None and el.text != "0":
            el.text = "0"
            changed = True
    return changed


def fix_zero_rated_breakdown_tax_amount(root, _issues):
    """aligned-ibrp-z-09: Zero rated VAT breakdown TaxAmount must be 0"""
    changed = False
    for sub in _find(root, "//cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cbc:ID='Z']"):
        el = sub.find(f"{CBC_}TaxAmount")
        if el is not None and el.text != "0":
            el.text = "0"
            changed = True
    return changed


def fix_n_breakdown_tax_amount(root, _issues):
    """ibr-108-ae: Standard additional VAT (N) breakdown TaxAmount must be 0"""
    changed = False
    for sub in _find(root, "//cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cbc:ID='N']"):
        el = sub.find(f"{CBC_}TaxAmount")
        if el is not None and el.text != "0":
            el.text = "0"
            changed = True
    return changed


def fix_exempt_line_vat_amount(root, _issues):
    """ibr-163-ae: Exempt line VAT amount shall not be present"""
    changed = False
    lines = (
        _find(root, "//cac:InvoiceLine[cac:Item/cac:ClassifiedTaxCategory/cbc:ID='E']") +
        _find(root, "//cac:CreditNoteLine[cac:Item/cac:ClassifiedTaxCategory/cbc:ID='E']")
    )
    for line in lines:
        for ext in line.findall(f".//{CAC_}ItemPriceExtension"):
            for tot in ext.findall(f"{CAC_}TaxTotal"):
                for amt in tot.findall(f"{CBC_}TaxAmount"):
                    tot.remove(amt)
                    changed = True
    return changed


def fix_zero_rated_line_vat_amount(root, _issues):
    """ibr-165-ae: Zero rated line VAT amount must be 0"""
    changed = False
    for line in _find(root, "//(cac:InvoiceLine|cac:CreditNoteLine)[cac:Item/cac:ClassifiedTaxCategory/cbc:ID='Z']"):
        for amt in line.findall(f".//{CBC_}TaxAmount"):
            if amt.text != "0":
                amt.text = "0"
                changed = True
    return changed


def fix_standard_breakdown_no_exemption(root, _issues):
    """aligned-ibrp-s-10: Standard rated breakdown must not have exemption reason"""
    changed = False
    for cat in _find(root, "//cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory[cbc:ID='S']"):
        for tag in ("TaxExemptionReason", "TaxExemptionReasonCode"):
            for el in cat.findall(f"{CBC_}{tag}"):
                cat.remove(el)
                changed = True
    return changed


def fix_item_classification_list_id(root, _issues):
    """ibr-188-ae: ItemClassificationCode listID must be 'HS'"""
    changed = False
    for el in _find(root, "//cac:CommodityClassification/cbc:ItemClassificationCode"):
        if el.get("listID") != "HS":
            el.set("listID", "HS")
            changed = True
    return changed


def fix_service_accounting_scheme_id(root, _issues):
    """ibr-189-ae: AdditionalItemIdentification/ID schemeID must be 'SAC'"""
    changed = False
    for el in _find(root, "//cac:AdditionalItemIdentification/cbc:ID"):
        if el.get("schemeID") != "SAC":
            el.set("schemeID", "SAC")
            changed = True
    return changed


def fix_seller_address(root, _issues):
    """ibr-143-ae: Seller PostalAddress must have StreetName, CityName, CountrySubentity"""
    changed = False
    for addr in _find(root, "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress"):
        for tag, placeholder in [("StreetName", "Placeholder Street"),
                                   ("CityName", "Dubai"),
                                   ("CountrySubentity", "DXB")]:
            if _find1(addr, f"cbc:{tag}") is None:
                addr.append(_el(tag, placeholder))
                changed = True
    return changed


def fix_buyer_address(root, _issues):
    """ibr-144-ae: Buyer PostalAddress must have StreetName, CityName, CountrySubentity"""
    changed = False
    for addr in _find(root, "//cac:AccountingCustomerParty/cac:Party/cac:PostalAddress"):
        for tag, placeholder in [("StreetName", "Placeholder Street"),
                                   ("CityName", "Dubai"),
                                   ("CountrySubentity", "DXB")]:
            if _find1(addr, f"cbc:{tag}") is None:
                addr.append(_el(tag, placeholder))
                changed = True
    return changed


def fix_uae_country_subdivision(root, _issues):
    """ibr-128-ae: Country subdivision must be valid emirate code when country is AE"""
    valid = {"AUH", "DXB", "SHJ", "UAQ", "FUJ", "AJM", "RAK"}
    changed = False
    for addr in _find(root, "//cac:PostalAddress[cac:Country/cbc:IdentificationCode='AE']"):
        sub = _find1(addr, "cbc:CountrySubentity")
        if sub is None:
            addr.append(_el("CountrySubentity", "DXB"))
            changed = True
        elif sub.text not in valid:
            sub.text = "DXB"
            changed = True
    return changed


def fix_item_description(root, _issues):
    """ibr-125-ae: Item Description must be present"""
    changed = False
    for item in _find(root, "//cac:Item[not(cbc:Description)]"):
        name = _find1(item, "cbc:Name")
        desc_text = name.text if (name is not None and name.text) else "Item Description"
        item.insert(0, _el("Description", desc_text))
        changed = True
    return changed


def fix_delivery_terms_id(root, _issues):
    """ibr-196-ae: DeliveryTerms/ID must be present"""
    changed = False
    for dt in _find(root, "//cac:DeliveryTerms[not(cbc:ID)]"):
        dt.insert(0, _el("ID", "PLACEHOLDER"))
        changed = True
    return changed


def fix_payment_account_credit_transfer(root, _issues):
    """ibr-192-ae: Credit transfer (code 30) must have PayeeFinancialAccount/ID"""
    changed = False
    for pm in _find(root, "//cac:PaymentMeans[cbc:PaymentMeansTypeCode='30']"):
        if _find1(pm, "cac:PayeeFinancialAccount/cbc:ID") is None:
            pfa = etree.SubElement(pm, f"{CAC_}PayeeFinancialAccount")
            pfa.append(_el("ID", "PLACEHOLDER-ACCOUNT"))
            changed = True
    return changed


def fix_net_price(root, _issues):
    """aligned-ibrp-004: Net price = Gross price - Discount"""
    changed = False
    for price in _find(root, "//cac:Price[cac:AllowanceCharge]"):
        net_el = price.find(f"{CBC_}PriceAmount")
        ac = price.find(f"{CAC_}AllowanceCharge")
        if net_el is None or ac is None:
            continue
        gross_el = ac.find(f"{CBC_}BaseAmount")
        disc_el = ac.find(f"{CBC_}Amount")
        if gross_el is None or disc_el is None:
            continue
        expected = _dec(gross_el.text) - _dec(disc_el.text)
        if _dec(net_el.text) != expected:
            net_el.text = _fmt(expected)
            changed = True
    return changed


def fix_allowance_charge_amounts(root, _issues):
    """ibr-131-ae / ibr-146-ae: Amount = BaseAmount * MultiplierFactor / 100"""
    changed = False
    for ac in _find(root, "//cac:AllowanceCharge[not(ancestor::cac:Price)]"):
        base_el = ac.find(f"{CBC_}BaseAmount")
        pct_el = ac.find(f"{CBC_}MultiplierFactorNumeric")
        amt_el = ac.find(f"{CBC_}Amount")
        if base_el is None or pct_el is None or amt_el is None:
            continue
        expected = (_dec(base_el.text) * _dec(pct_el.text) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        if _dec(amt_el.text) != expected:
            amt_el.text = str(expected)
            changed = True
    return changed


def fix_vat_breakdown_amounts(root, _issues):
    """
    aligned-ibrp-s-08/09, aligned-ibrp-e-08, aligned-ibrp-z-08, ibr-102-ae:
    Recalculate TaxSubtotal TaxableAmount and TaxAmount from line items.
    """
    changed = False
    curr = _currency(root)

    for subtotal in _find(root, "//cac:TaxTotal/cac:TaxSubtotal"):
        cat_el = _find1(subtotal, "cac:TaxCategory/cbc:ID")
        rate_el = _find1(subtotal, "cac:TaxCategory/cbc:Percent")
        taxable_el = subtotal.find(f"{CBC_}TaxableAmount")
        tax_amt_el = subtotal.find(f"{CBC_}TaxAmount")

        if cat_el is None or taxable_el is None:
            continue

        cat_id = cat_el.text.strip()
        rate = _dec(rate_el.text) if rate_el is not None else Decimal("0")

        # Sum line extensions for this category + rate
        total = Decimal("0")
        for line in _find(root, "//cac:InvoiceLine | //cac:CreditNoteLine"):
            line_cat = _find1(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID")
            line_rate = _find1(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent")
            line_ext = _find1(line, "cbc:LineExtensionAmount")
            if line_cat is None or line_ext is None:
                continue
            if line_cat.text.strip() != cat_id:
                continue
            if rate_el is not None and line_rate is not None and _dec(line_rate.text) != rate:
                continue
            total += _dec(line_ext.text)

        # Add document-level charges, subtract allowances for this category
        for ac in _find(root, "//cac:AllowanceCharge[not(ancestor::cac:Price)]"):
            ac_cat = _find1(ac, "cac:TaxCategory/cbc:ID")
            charge_el = ac.find(f"{CBC_}ChargeIndicator")
            amt_el = ac.find(f"{CBC_}Amount")
            if ac_cat is None or charge_el is None or amt_el is None:
                continue
            if ac_cat.text.strip() != cat_id:
                continue
            if charge_el.text.lower() == "true":
                total += _dec(amt_el.text)
            else:
                total -= _dec(amt_el.text)

        new_taxable = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if abs(_dec(taxable_el.text) - new_taxable) > Decimal("0.02"):
            taxable_el.text = _fmt(new_taxable)
            changed = True

        # Recalculate TaxAmount based on category
        if tax_amt_el is not None:
            if cat_id in ("E", "Z", "O", "N"):
                if tax_amt_el.text != "0":
                    tax_amt_el.text = "0"
                    changed = True
            else:
                expected_tax = (abs(new_taxable) * rate / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP)
                if abs(_dec(tax_amt_el.text) - expected_tax) > Decimal("0.02"):
                    tax_amt_el.text = _fmt(expected_tax)
                    changed = True

    return changed


def fix_standard_vat_amount(root, _issues):
    """aligned-ibrp-s-09: VAT TaxAmount = TaxableAmount * Rate / 100"""
    changed = False
    for subtotal in _find(root, "//cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cbc:ID='S']"):
        taxable_el = subtotal.find(f"{CBC_}TaxableAmount")
        tax_amt_el = subtotal.find(f"{CBC_}TaxAmount")
        rate_el = _find1(subtotal, "cac:TaxCategory/cbc:Percent")
        if taxable_el is None or tax_amt_el is None or rate_el is None:
            continue
        expected = (abs(_dec(taxable_el.text)) * _dec(rate_el.text) / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        if abs(_dec(tax_amt_el.text)) != expected:
            tax_amt_el.text = _fmt(expected)
            changed = True
    return changed


def fix_line_price_extension(root, _issues):
    """ibr-194-ae / ibr-104-ae: Add ItemPriceExtension Amount (BTAE-10) and TaxAmount (BTAE-08) derived from LineExtensionAmount and VAT rate"""
    changed = False
    curr = _currency(root)

    for line in _find(root, "//cac:InvoiceLine | //cac:CreditNoteLine"):
        line_ext_el = line.find(f"{CBC_}LineExtensionAmount")
        if line_ext_el is None:
            continue
        line_ext = _dec(line_ext_el.text)

        cat_el  = _find1(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID")
        rate_el = _find1(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent")
        cat_id  = (cat_el.text or "S").strip() if cat_el is not None else "S"
        rate    = _dec(rate_el.text) if rate_el is not None else Decimal("0")

        # Find or create ItemPriceExtension
        ipe = line.find(f"{CAC_}ItemPriceExtension")
        if ipe is None:
            ipe = etree.SubElement(line, f"{CAC_}ItemPriceExtension")
            changed = True

        # BTAE-10: Amount = LineExtensionAmount
        amt_el = ipe.find(f"{CBC_}Amount")
        if amt_el is None:
            amt_el = etree.SubElement(ipe, f"{CBC_}Amount")
            amt_el.set("currencyID", curr)
            amt_el.text = _fmt(line_ext)
            changed = True

        # BTAE-08: TaxAmount — required when VAT category is not Exempt (E)
        if cat_id != "E":
            tax_total = ipe.find(f"{CAC_}TaxTotal")
            if tax_total is None:
                tax_total = etree.SubElement(ipe, f"{CAC_}TaxTotal")
                changed = True

            tax_amt_el = tax_total.find(f"{CBC_}TaxAmount")
            if tax_amt_el is None:
                tax_amt_el = etree.SubElement(tax_total, f"{CBC_}TaxAmount")
                tax_amt_el.set("currencyID", curr)
                # S → rate%; Z / O / AE / N → 0
                if cat_id == "S" and rate > 0:
                    vat_amt = (line_ext * rate / Decimal("100")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    vat_amt = Decimal("0")
                tax_amt_el.text = _fmt(vat_amt)
                changed = True

    return changed


def _doc_type_code(root) -> str:
    """Return the document type code string (e.g. '381', '380') regardless of element name."""
    for xpath in ("/*/cbc:CreditNoteTypeCode", "/*/cbc:InvoiceTypeCode"):
        el = _find1(root, xpath)
        if el is not None:
            return (el.text or "").strip()
    return ""


def fix_credit_note_reason_code(root, _issues):
    """ibr-158-ae: DiscrepancyResponse/ResponseCode (BTAE-03) must be present for credit notes (type 381)"""
    if _doc_type_code(root) != "381":
        return False
    if _find1(root, "/*/cac:DiscrepancyResponse/cbc:ResponseCode") is not None:
        return False
    dr = _cac("DiscrepancyResponse")
    rc = etree.SubElement(dr, f"{CBC_}ResponseCode")
    rc.text = "DL8.61.1.A"
    # Insert after InvoicePeriod if present, else after BuyerReference, else before OrderReference
    anchor = next((el for el in [
        _find1(root, "/*/cac:InvoicePeriod"),
        _find1(root, "/*/cbc:BuyerReference"),
        _find1(root, "/*/cac:OrderReference"),
    ] if el is not None), None)
    if anchor is not None:
        anchor.addnext(dr)
    else:
        root.append(dr)
    return True


def fix_billing_reference(root, _issues):
    """ibr-055-ae: Add placeholder BillingReference for credit notes unless reason code is VD"""
    if _doc_type_code(root) not in ("381", "81"):
        return False
    reason = _find1(root, "/*/cac:DiscrepancyResponse/cbc:ResponseCode")
    if reason is not None and reason.text == "VD":
        return False
    if _find1(root, "/*/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID") is not None:
        return False
    br = _cac("BillingReference")
    idr = etree.SubElement(br, f"{CAC_}InvoiceDocumentReference")
    id_el = etree.SubElement(idr, f"{CBC_}ID")
    id_el.text = "PLACEHOLDER-INVOICE-REF"
    anchor = next((el for el in [
        _find1(root, "/*/cac:OrderReference"),
        _find1(root, "/*/cac:DiscrepancyResponse"),
        _find1(root, "/*/cac:DespatchDocumentReference"),
    ] if el is not None), None)
    if anchor is not None:
        anchor.addnext(br)
    else:
        root.append(br)
    return True


def fix_payment_means(root, _issues):
    """ibr-191-ae: PaymentMeans (code 1 = instrument not defined) required for non-credit-note invoices"""
    if _doc_type_code(root) in ("81", "381", "261"):
        return False
    import re
    profile_el = _find1(root, "/*/cbc:ProfileExecutionID")
    if profile_el is not None and re.match(r"^[01]1[01]{6}$", (profile_el.text or "")):
        return False  # Deemed supply — exempt
    if _find1(root, "/*/cac:PaymentMeans/cbc:PaymentMeansCode") is not None:
        return False
    pm = _cac("PaymentMeans")
    code_el = etree.SubElement(pm, f"{CBC_}PaymentMeansCode")
    code_el.text = "1"
    # Insert before AllowanceCharge or TaxTotal, whichever comes first
    anchor = next((el for el in [
        _find1(root, "/*/cac:PaymentTerms"),
        _find1(root, "/*/cac:AllowanceCharge"),
        _find1(root, "/*/cac:TaxTotal"),
    ] if el is not None), None)
    if anchor is not None:
        anchor.addprevious(pm)
    else:
        root.append(pm)
    return True


def fix_seller_legal_entity_scheme(root, _issues):
    """ibr-181-ae / ibr-173-ae: Add schemeAgencyID='TL' and schemeAgencyName to Seller CompanyID when missing"""
    changed = False
    for party in _find(root, "//cac:AccountingSupplierParty/cac:Party"):
        endpoint = _find1(party, "cbc:EndpointID[@schemeID='0235']")
        company = _find1(party, "cac:PartyLegalEntity/cbc:CompanyID")
        if company is None:
            continue
        if not company.get("schemeAgencyID"):
            company.set("schemeAgencyID", "TL")
            changed = True
        if company.get("schemeAgencyID") == "TL" and not company.get("schemeAgencyName"):
            company.set("schemeAgencyName", "Trade License issuing Authority")
            changed = True
    return changed


def fix_seller_authority_name(root, _issues):
    """ibr-172-ae: Add schemeAgencyName when Seller CompanyID schemeAgencyID is TL"""
    changed = False
    for company in _find(root, "//cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID[@schemeAgencyID='TL']"):
        if not company.get("schemeAgencyName"):
            company.set("schemeAgencyName", "Trade License issuing Authority")
            changed = True
    return changed


def fix_buyer_legal_entity_scheme(root, _issues):
    """ibr-180-ae / ibr-183-ae: Add schemeAgencyID='TL' and schemeAgencyName to Buyer CompanyID when missing"""
    changed = False
    for party in _find(root, "//cac:AccountingCustomerParty/cac:Party"):
        company = _find1(party, "cac:PartyLegalEntity/cbc:CompanyID")
        if company is None:
            continue
        endpoint = _find1(party, "cbc:EndpointID[@schemeID='0235']")
        if endpoint is None:
            continue
        if not company.get("schemeAgencyID"):
            company.set("schemeAgencyID", "TL")
            changed = True
        if company.get("schemeAgencyID") == "TL" and not company.get("schemeAgencyName"):
            company.set("schemeAgencyName", "Trade License issuing Authority")
            changed = True
    return changed


def fix_buyer_authority_name(root, _issues):
    """ibr-101-ae: Add schemeAgencyName when Buyer CompanyID schemeAgencyID is TL"""
    changed = False
    for company in _find(root, "//cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID[@schemeAgencyID='TL']"):
        if not company.get("schemeAgencyName"):
            company.set("schemeAgencyName", "Trade License issuing Authority")
            changed = True
    return changed


def fix_price_base_quantity_and_gross(root, _issues):
    """ibr-126-ae: Add BaseQuantity=1 and AllowanceCharge/BaseAmount to Price when missing"""
    changed = False
    curr = _currency(root)

    for line in _find(root, "//cac:InvoiceLine | //cac:CreditNoteLine"):
        price = line.find(f"{CAC_}Price")
        if price is None:
            continue

        # Fix BaseQuantity
        if price.find(f"{CBC_}BaseQuantity") is None:
            qty_el = (line.find(f"{CBC_}InvoicedQuantity") or
                      line.find(f"{CBC_}CreditedQuantity"))
            unit = qty_el.get("unitCode", "C62") if qty_el is not None else "C62"
            bq = _el("BaseQuantity", "1", attrib={"unitCode": unit})
            price_amt = price.find(f"{CBC_}PriceAmount")
            if price_amt is not None:
                price_amt.addnext(bq)
            else:
                price.append(bq)
            changed = True

        # Fix AllowanceCharge/BaseAmount
        ac = price.find(f"{CAC_}AllowanceCharge")
        if ac is None:
            # No AllowanceCharge at all — create one with zero discount
            price_amt_el = price.find(f"{CBC_}PriceAmount")
            gross = _dec(price_amt_el.text) if price_amt_el is not None else Decimal("0")
            ac = etree.SubElement(price, f"{CAC_}AllowanceCharge")
            ci = etree.SubElement(ac, f"{CBC_}ChargeIndicator"); ci.text = "false"
            am = etree.SubElement(ac, f"{CBC_}Amount");       am.set("currencyID", curr); am.text = "0.00"
            ba = etree.SubElement(ac, f"{CBC_}BaseAmount");   ba.set("currencyID", curr); ba.text = _fmt(gross)
            changed = True
        elif ac.find(f"{CBC_}BaseAmount") is None:
            # AllowanceCharge exists but no BaseAmount — gross = net + discount
            price_amt_el = price.find(f"{CBC_}PriceAmount")
            disc_el = ac.find(f"{CBC_}Amount")
            net  = _dec(price_amt_el.text) if price_amt_el is not None else Decimal("0")
            disc = _dec(disc_el.text)      if disc_el is not None       else Decimal("0")
            gross = net + disc
            ba = _el("BaseAmount", _fmt(gross), attrib={"currencyID": curr})
            ac.append(ba)
            changed = True

    return changed


def fix_exchange_rate_decimals(root, _issues):
    """ibr-002-ae: Exchange rate max 6 decimal places"""
    import re
    changed = False
    for el in _find(root, "//cac:TaxExchangeRate/cbc:CalculationRate"):
        text = (el.text or "").strip()
        if re.match(r"^[0-9]+\.[0-9]{7,}$", text):
            el.text = _fmt(_dec(text), places=6)
            changed = True
    return changed


# ── Rule → fix function registry ─────────────────────────────────────────────

RULE_FIXES: dict[str, callable] = {
    "aligned-ibrp-001-ae":  fix_customization_id,
    "aligned-ibrp-002-ae":  fix_profile_id,
    "ibr-154-ae":           fix_profile_execution_id,
    "ibr-140-ae":           fix_tax_currency_code,
    "ibr-193-ae":           fix_uuid,
    "ibr-124-ae":           fix_remove_tax_point_date_creditnote,
    # VAT rates
    "ibr-190-ae":           fix_standard_vat_rate,
    "aligned-ibrp-s-05":   fix_standard_vat_rate,
    "aligned-ibrp-s-06":   fix_standard_vat_rate,
    "aligned-ibrp-s-07":   fix_standard_vat_rate,
    "aligned-ibrp-e-05":   fix_exempt_line_percent,
    "aligned-ibrp-e-06":   fix_exempt_allowance_charge_percent,
    "aligned-ibrp-e-07":   fix_exempt_allowance_charge_percent,
    "aligned-ibrp-z-05":   fix_zero_rated_percent,
    "aligned-ibrp-z-06":   fix_zero_rated_percent,
    "aligned-ibrp-z-07":   fix_zero_rated_percent,
    "ibr-120-ae":           fix_zero_rated_percent,
    "ibr-121-ae":           fix_exempt_breakdown_percent,
    # VAT amounts
    "aligned-ibrp-e-09":   fix_exempt_breakdown_tax_amount,
    "aligned-ibrp-z-09":   fix_zero_rated_breakdown_tax_amount,
    "ibr-108-ae":           fix_n_breakdown_tax_amount,
    "ibr-163-ae":           fix_exempt_line_vat_amount,
    "ibr-165-ae":           fix_zero_rated_line_vat_amount,
    "aligned-ibrp-s-10":   fix_standard_breakdown_no_exemption,
    # VAT breakdown recalculations
    "aligned-ibrp-s-08":   fix_vat_breakdown_amounts,
    "aligned-ibrp-s-09":   fix_standard_vat_amount,
    "aligned-ibrp-e-08":   fix_vat_breakdown_amounts,
    "aligned-ibrp-z-08":   fix_vat_breakdown_amounts,
    "ibr-102-ae":           fix_vat_breakdown_amounts,
    # Price calculations
    "aligned-ibrp-004":    fix_net_price,
    "ibr-131-ae":           fix_allowance_charge_amounts,
    "ibr-146-ae":           fix_allowance_charge_amounts,
    # Attribute corrections
    "ibr-188-ae":           fix_item_classification_list_id,
    "ibr-189-ae":           fix_service_accounting_scheme_id,
    # Address / placeholder fixes
    "ibr-143-ae":           fix_seller_address,
    "ibr-144-ae":           fix_buyer_address,
    "ibr-128-ae":           fix_uae_country_subdivision,
    "ibr-125-ae":           fix_item_description,
    "ibr-196-ae":           fix_delivery_terms_id,
    "ibr-192-ae":           fix_payment_account_credit_transfer,
    # Exchange rate
    "ibr-002-ae":           fix_exchange_rate_decimals,
    # Line price extension (BTAE-10 / BTAE-08)
    "ibr-194-ae":           fix_line_price_extension,
    "ibr-104-ae":           fix_line_price_extension,
    # Credit note structure
    "ibr-158-ae":           fix_credit_note_reason_code,
    "ibr-055-ae":           fix_billing_reference,
    # Payment means
    "ibr-191-ae":           fix_payment_means,
    # Seller legal entity scheme type
    "ibr-181-ae":           fix_seller_legal_entity_scheme,
    "ibr-173-ae":           fix_seller_legal_entity_scheme,
    "ibr-172-ae":           fix_seller_authority_name,
    # Buyer legal entity scheme type
    "ibr-180-ae":           fix_buyer_legal_entity_scheme,
    "ibr-183-ae":           fix_buyer_legal_entity_scheme,
    "ibr-101-ae":           fix_buyer_authority_name,
    # Price details
    "ibr-126-ae":           fix_price_base_quantity_and_gross,
}

# Rules that cannot be auto-fixed (need real business data)
UNFIXABLE_RULES = {
    "ibr-010-ae":    "Passport issuing country code requires actual country data",
    "ibr-012-ae":    "Passport issuing country code requires actual country data",
    "ibr-134-ae":    "Seller VAT Identifier (IBT-031) requires actual VAT registration number",
    "ibr-177-ae":    "Seller VAT or tax registration identifier requires actual registration data",
    "ibr-135-ae":    "Buyer identifier/VAT requires actual buyer registration data",
    "ibr-149-ae":    "Buyer legal registration identifier requires actual registration data",
    "ibr-150-ae":    "Seller legal registration identifier requires actual registration data",
    "ibr-141-ae":    "TaxPointDate must be before IssueDate — adjust the date manually",
    "ibr-159-ae":    "Currency exchange rate (BTAE-04) requires actual exchange rate",
    "ibr-153-ae":    "Exchange rate source/target currency requires actual rate data",
    "ibr-175-ae":    "Multi-currency AED totals require actual AED amounts",
    "ibr-136-ae":    "Buyer legal registration ID for type 480/81 requires actual ID",
    "ibr-137-ae":    "Principle ID (BTAE-14) for Disclosed Agent billing requires actual ID",
    "ibr-147-ae":    "Line net amount mismatch — check quantity, price and allowances",
    "ibr-176-ae":    "Seller VAT ID and Principle ID must differ — update one of them",
    "ibr-007-ae":    "Beneficiary ID (BTAE-01) for Free Trade Zone requires actual ID",
    "ibr-138-ae":    "InvoicePeriod required for Summary invoice — add actual period",
    "ibr-142-ae":    "Delivery address required for E-commerce — add actual address",
    "ibr-152-ae":    "Delivery address required for Exports — add actual address",
    "ibr-160-ae":    "Invoice note required when billing frequency is 'Others'",
    "ibr-127-ae":    "DueDate required when PayableAmount > 0 — add actual due date",
    "ibr-166-ae":    "Type of goods/services (BTAE-09) for Reverse charge requires actual value",
    "ibr-184-ae":    "Item classification code (HS) required for Goods type",
    "ibr-185-ae":    "Service accounting code required for Services type",
    "ibr-186-ae":    "Both classification code and SAC required for 'Both' item type",
}


# ── Fix engine ────────────────────────────────────────────────────────────────

@dataclass
class FixResult:
    xml_file: str
    output_file: str
    initial_issue_count: int
    final_issue_count: int
    rounds: int
    applied_fixes: list[str] = field(default_factory=list)
    unfixable: list[str] = field(default_factory=list)
    final_valid: bool = False


def fix_document(xml_path: Path) -> FixResult:
    xml_path = xml_path.resolve()
    if not xml_path.exists():
        raise FileNotFoundError(f"File not found: {xml_path}")

    # Output path: <stem>_valid.xml in same directory
    out_path = xml_path.parent / f"{xml_path.stem}_valid.xml"

    # Parse with lxml (preserve original encoding)
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    # Initial validation
    initial_result = validate(xml_path)
    initial_count = initial_result.fatal_count

    if initial_result.is_valid:
        # Nothing to fix — just copy
        tree.write(str(out_path), xml_declaration=True, encoding="UTF-8", pretty_print=True)
        return FixResult(
            xml_file=str(xml_path),
            output_file=str(out_path),
            initial_issue_count=0,
            final_issue_count=0,
            rounds=0,
            final_valid=True,
        )

    applied_fixes: list[str] = []
    unfixable_seen: dict[str, str] = {}
    current_issues = initial_result.issues

    for round_num in range(1, MAX_ROUNDS + 1):
        fatal_issues = [i for i in current_issues if i.flag == "fatal"]
        if not fatal_issues:
            break

        changed_this_round = False
        tried_rules: set[str] = set()

        for issue in fatal_issues:
            rule_id = issue.rule_id
            if rule_id in tried_rules:
                continue
            tried_rules.add(rule_id)

            if rule_id in RULE_FIXES:
                fix_fn = RULE_FIXES[rule_id]
                if fix_fn(root, current_issues):
                    applied_fixes.append(f"[Round {round_num}] {rule_id}: {fix_fn.__doc__.split(chr(10))[0].strip()}")
                    changed_this_round = True
            elif rule_id in UNFIXABLE_RULES:
                if rule_id not in unfixable_seen:
                    unfixable_seen[rule_id] = UNFIXABLE_RULES[rule_id]
            # unknown rule IDs are silently skipped

        if not changed_this_round:
            break

        # Write to temp output and re-validate
        tree.write(str(out_path), xml_declaration=True, encoding="UTF-8", pretty_print=True)
        re_result = validate(out_path)
        current_issues = re_result.issues

        if re_result.is_valid:
            break

    # Final write
    tree.write(str(out_path), xml_declaration=True, encoding="UTF-8", pretty_print=True)
    final_result = validate(out_path)

    return FixResult(
        xml_file=str(xml_path),
        output_file=str(out_path),
        initial_issue_count=initial_count,
        final_issue_count=final_result.fatal_count,
        rounds=round_num if initial_count > 0 else 0,
        applied_fixes=applied_fixes,
        unfixable=list(unfixable_seen.values()),
        final_valid=final_result.is_valid,
    )


# ── CLI output ────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

def _c(text, code, use_color):
    return f"{code}{text}{RESET}" if use_color else text


def print_fix_result(result: FixResult, use_color: bool = True) -> None:
    c = lambda t, code: _c(t, code, use_color)

    print()
    print(c("=" * 64, BOLD))
    print(c("  PINT AE Auto-Fix Report", BOLD))
    print(c("=" * 64, BOLD))
    print(f"  Input   : {result.xml_file}")
    print(f"  Output  : {result.output_file}")
    print(f"  Rounds  : {result.rounds}")
    print(f"  Fatals  : {result.initial_issue_count} -> {result.final_issue_count}")

    if result.final_valid:
        print(f"  Status  : {c('VALID', GREEN + BOLD)}")
    else:
        remaining = result.final_issue_count
        print(f"  Status  : {c(f'STILL INVALID ({remaining} fatal error(s) remain)', RED + BOLD)}")

    if result.applied_fixes:
        print()
        print(c("  Applied fixes:", CYAN + BOLD))
        for fix in result.applied_fixes:
            print(f"    {c('[OK]', GREEN)} {fix}")

    if result.unfixable:
        print()
        print(c("  Unfixable (require manual correction):", YELLOW + BOLD))
        for msg in result.unfixable:
            print(f"    {c('[!]', YELLOW)} {msg}")

    print()
    print(c("=" * 64, BOLD))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Auto-fix a UBL Invoice or CreditNote against PINT AE (UAE) rules "
            "and save the result as <name>_valid.xml"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix.py invoice.xml
  python fix.py "path/to/my invoice.xml"
  python fix.py invoice.xml --no-color
""",
    )
    parser.add_argument("xml_file", help="Path to UBL Invoice or CreditNote XML file")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()
    use_color = not args.no_color and sys.stdout.isatty()

    try:
        result = fix_document(Path(args.xml_file))
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 2

    print_fix_result(result, use_color=use_color)
    return 0 if result.final_valid else 1


if __name__ == "__main__":
    sys.exit(main())
