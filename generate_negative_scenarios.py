#!/usr/bin/env python3
"""
Generate negative-scenario XML files for PINT AE schematron validation testing.
  Seller endpoint : 1000454545
  Buyer endpoint  : 1000464646

Run:  python generate_negative_scenarios.py
Output: negative-xml-scenarios/  (50+ files, organised by category)
"""

from pathlib import Path

OUT = Path(__file__).parent / "negative-xml-scenarios"
OUT.mkdir(exist_ok=True)

SELLER = "1000454545"
BUYER  = "1000464646"

INV_NS = 'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"'
CN_NS  = 'xmlns="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"'
COMMON = (
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"\n'
    '         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
)

FILES = []   # (filename, description)

def write(name: str, xml: str, description: str):
    (OUT / name).write_text(xml, encoding="utf-8")
    FILES.append((name, description))


# ─────────────────────────────────────────────────────────────────────────────
#  VALID BASE (380 / Standard 00000000 / VAT S)  – used as starting template
# ─────────────────────────────────────────────────────────────────────────────
def valid_invoice(id_val="INV-2025-NEG-BASE"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>{id_val}</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:TaxPointDate>2025-05-31</cbc:TaxPointDate>
  <cbc:DueDate>2025-06-15</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:PaymentMeans>
    <cbc:PaymentMeansCode>30</cbc:PaymentMeansCode>
    <cac:PayeeFinancialAccount>
      <cbc:ID>AE070331234567890123456</cbc:ID>
    </cac:PayeeFinancialAccount>
  </cac:PaymentMeans>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Standard rated supply</cbc:Description>
      <cbc:Name>Test Item</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
      <cac:AllowanceCharge>
        <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
        <cbc:Amount currencyID="AED">0.00</cbc:Amount>
        <cbc:BaseAmount currencyID="AED">100.00</cbc:BaseAmount>
      </cac:AllowanceCharge>
    </cac:Price>
    <cac:ItemPriceExtension>
      <cbc:Amount currencyID="AED">1050.00</cbc:Amount>
      <cac:TaxTotal>
        <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      </cac:TaxTotal>
    </cac:ItemPriceExtension>
  </cac:InvoiceLine>
</Invoice>"""

def valid_credit_note(id_val="CN-2025-NEG-BASE"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CreditNote {CN_NS}
            {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>{id_val}</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:CreditNoteTypeCode>381</cbc:CreditNoteTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:DiscrepancyResponse>
    <cbc:ResponseCode>CD</cbc:ResponseCode>
  </cac:DiscrepancyResponse>
  <cac:BillingReference>
    <cac:InvoiceDocumentReference>
      <cbc:ID>INV-2025-000</cbc:ID>
    </cac:InvoiceDocumentReference>
  </cac:BillingReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:CreditNoteLine>
    <cbc:ID>1</cbc:ID>
    <cbc:CreditedQuantity unitCode="H87">10</cbc:CreditedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Standard rated supply</cbc:Description>
      <cbc:Name>Test Item</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
      <cac:AllowanceCharge>
        <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
        <cbc:Amount currencyID="AED">0.00</cbc:Amount>
        <cbc:BaseAmount currencyID="AED">100.00</cbc:BaseAmount>
      </cac:AllowanceCharge>
    </cac:Price>
    <cac:ItemPriceExtension>
      <cbc:Amount currencyID="AED">1050.00</cbc:Amount>
      <cac:TaxTotal>
        <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      </cac:TaxTotal>
    </cac:ItemPriceExtension>
  </cac:CreditNoteLine>
</CreditNote>"""


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 1 – MISSING MANDATORY HEADER FIELDS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-001-missing-invoice-id.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-001: Missing cbc:ID (IBT-001) — invoice has no document number -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <!-- cbc:ID deliberately omitted -->
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:TaxPointDate>2025-05-31</cbc:TaxPointDate>
  <cbc:DueDate>2025-06-15</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Standard rated supply</cbc:Description>
      <cbc:Name>Test Item</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
    </cac:Price>
    <cac:ItemPriceExtension>
      <cbc:Amount currencyID="AED">1050.00</cbc:Amount>
      <cac:TaxTotal><cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount></cac:TaxTotal>
    </cac:ItemPriceExtension>
  </cac:InvoiceLine>
</Invoice>""",
"Missing cbc:ID (IBT-001) — no invoice document number")

# ── NEG-002 ──────────────────────────────────────────────────────────────────
write("neg-002-missing-issue-date.xml", valid_invoice("INV-2025-NEG-002").replace(
    "  <cbc:IssueDate>2025-06-01</cbc:IssueDate>\n", "  <!-- cbc:IssueDate omitted -->\n"),
"Missing cbc:IssueDate (IBT-002)")

# ── NEG-003 ──────────────────────────────────────────────────────────────────
write("neg-003-missing-type-code.xml", valid_invoice("INV-2025-NEG-003").replace(
    "  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>\n", "  <!-- cbc:InvoiceTypeCode omitted -->\n"),
"Missing cbc:InvoiceTypeCode (IBT-003)")

# ── NEG-004 ──────────────────────────────────────────────────────────────────
write("neg-004-missing-currency-code.xml", valid_invoice("INV-2025-NEG-004").replace(
    "  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>\n", "  <!-- DocumentCurrencyCode omitted -->\n"),
"Missing cbc:DocumentCurrencyCode (IBT-005)")

# ── NEG-005 ──────────────────────────────────────────────────────────────────
write("neg-005-missing-customization-id.xml", valid_invoice("INV-2025-NEG-005").replace(
    "  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>\n", "  <!-- CustomizationID omitted -->\n"),
"Missing cbc:CustomizationID (IBT-024)")

# ── NEG-006 ──────────────────────────────────────────────────────────────────
write("neg-006-missing-profile-execution-id.xml", valid_invoice("INV-2025-NEG-006").replace(
    "  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>\n", "  <!-- ProfileExecutionID (BTAE-02) omitted -->\n"),
"Missing cbc:ProfileExecutionID (BTAE-02)")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 2 – MISSING MANDATORY SELLER FIELDS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-007-missing-seller-endpoint.xml", valid_invoice("INV-2025-NEG-007").replace(
    f"      <cbc:EndpointID schemeID=\"0235\">{SELLER}</cbc:EndpointID>\n",
    "      <!-- Seller EndpointID (IBT-034) omitted -->\n", 1),
"Missing seller EndpointID (IBT-034)")

write("neg-008-missing-seller-street.xml", valid_invoice("INV-2025-NEG-008").replace(
    "        <cbc:StreetName>Main Street</cbc:StreetName>\n",
    "        <!-- StreetName (IBT-035 / BTAE-04) omitted -->\n"),
"Missing seller StreetName (IBT-035 / BTAE-04)")

write("neg-009-missing-seller-city.xml", valid_invoice("INV-2025-NEG-009").replace(
    "        <cbc:CityName>Dubai</cbc:CityName>\n",
    "        <!-- CityName (IBT-037 / BTAE-05) omitted -->\n"),
"Missing seller CityName (IBT-037 / BTAE-05)")

write("neg-010-missing-seller-country-subentity.xml", valid_invoice("INV-2025-NEG-010").replace(
    "        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>\n",
    "        <!-- CountrySubentity (IBT-039 / BTAE-06) omitted -->\n"),
"Missing seller CountrySubentity (IBT-039 / BTAE-06)")

write("neg-011-missing-seller-vat-trn.xml", valid_invoice("INV-2025-NEG-011").replace(
    """      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
""", "      <!-- Seller PartyTaxScheme (IBT-031 / BTAE-11) omitted -->\n"),
"Missing seller PartyTaxScheme/CompanyID (IBT-031 / BTAE-11)")

write("neg-012-missing-seller-registration-name.xml", valid_invoice("INV-2025-NEG-012").replace(
    "        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>\n",
    "        <!-- Seller RegistrationName (IBT-027) omitted -->\n"),
"Missing seller RegistrationName (IBT-027)")

write("neg-013-missing-seller-trade-license.xml", valid_invoice("INV-2025-NEG-013").replace(
    '        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>\n',
    "        <!-- Seller Trade License CompanyID (BTAE-12/BTAE-15) omitted -->\n"),
"Missing seller Trade License CompanyID (BTAE-12 / BTAE-15)")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 3 – MISSING MANDATORY BUYER FIELDS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-014-missing-buyer-endpoint.xml", valid_invoice("INV-2025-NEG-014").replace(
    f"      <cbc:EndpointID schemeID=\"0235\">{BUYER}</cbc:EndpointID>\n",
    "      <!-- Buyer EndpointID (IBT-049) omitted -->\n"),
"Missing buyer EndpointID (IBT-049)")

write("neg-015-missing-buyer-registration-name.xml", valid_invoice("INV-2025-NEG-015").replace(
    "        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>\n",
    "        <!-- Buyer RegistrationName (IBT-044) omitted -->\n"),
"Missing buyer RegistrationName (IBT-044)")

write("neg-016-missing-buyer-trade-license.xml", valid_invoice("INV-2025-NEG-016").replace(
    '        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>\n',
    "        <!-- Buyer Trade License CompanyID (BTAE-13/BTAE-16) omitted -->\n"),
"Missing buyer Trade License CompanyID (BTAE-13 / BTAE-16)")

write("neg-017-ae-vat-missing-buyer-vat-trn.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-017: VAT category AE — buyer PartyTaxScheme (IBT-048) is mandatory but missing -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>INV-2025-NEG-017</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:TaxPointDate>2025-05-31</cbc:TaxPointDate>
  <cbc:DueDate>2025-06-15</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <!-- Buyer PartyTaxScheme (IBT-048) omitted — MANDATORY when VAT=AE -->
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>AE</cbc:ID>
        <cbc:Percent>0</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1000.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1000.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Reverse charge supply</cbc:Description>
      <cbc:Name>Test Item AE</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>AE</cbc:ID>
        <cbc:Percent>0</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
    </cac:Price>
    <cac:ItemPriceExtension>
      <cbc:Amount currencyID="AED">1000.00</cbc:Amount>
      <cac:TaxTotal><cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount></cac:TaxTotal>
    </cac:ItemPriceExtension>
  </cac:InvoiceLine>
</Invoice>""",
"VAT AE present but buyer PartyTaxScheme (IBT-048) is missing")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 4 – MISSING MANDATORY LINE FIELDS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-018-missing-line-id.xml", valid_invoice("INV-2025-NEG-018").replace(
    "    <cbc:ID>1</cbc:ID>\n    <cbc:InvoicedQuantity",
    "    <!-- Line ID (IBT-126) omitted -->\n    <cbc:InvoicedQuantity"),
"Missing InvoiceLine/cbc:ID (IBT-126)")

write("neg-019-missing-item-name.xml", valid_invoice("INV-2025-NEG-019").replace(
    "      <cbc:Name>Test Item</cbc:Name>\n",
    "      <!-- Item Name (IBT-153) omitted -->\n"),
"Missing Item/cbc:Name (IBT-153)")

write("neg-020-missing-item-description.xml", valid_invoice("INV-2025-NEG-020").replace(
    "      <cbc:Description>Standard rated supply</cbc:Description>\n",
    "      <!-- Item Description (IBT-154 / ibr-125-ae) omitted -->\n"),
"Missing Item/cbc:Description (IBT-154 / ibr-125-ae)")

write("neg-021-missing-line-extension-amount.xml", valid_invoice("INV-2025-NEG-021").replace(
    '    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>\n    <cac:Item>',
    '    <!-- LineExtensionAmount (IBT-131) omitted -->\n    <cac:Item>'),
"Missing InvoiceLine/cbc:LineExtensionAmount (IBT-131)")

write("neg-022-missing-invoiced-quantity.xml", valid_invoice("INV-2025-NEG-022").replace(
    '    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>\n',
    '    <!-- InvoicedQuantity (IBT-129) omitted -->\n'),
"Missing InvoiceLine/cbc:InvoicedQuantity (IBT-129)")

write("neg-023-missing-base-quantity.xml", valid_invoice("INV-2025-NEG-023").replace(
    '      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>\n',
    '      <!-- BaseQuantity (IBT-149 / ibr-126-ae) omitted -->\n'),
"Missing Price/cbc:BaseQuantity (IBT-149 / ibr-126-ae)")

write("neg-024-missing-item-price-extension.xml", valid_invoice("INV-2025-NEG-024").replace(
    """    <cac:ItemPriceExtension>
      <cbc:Amount currencyID="AED">1050.00</cbc:Amount>
      <cac:TaxTotal>
        <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      </cac:TaxTotal>
    </cac:ItemPriceExtension>
""", "    <!-- ItemPriceExtension (BTAE-08/BTAE-10) omitted — mandatory for S/AE/Z -->\n"),
"Missing ItemPriceExtension (BTAE-08 / BTAE-10) for VAT=S")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 5 – MISSING TAX / MONETARY TOTAL SECTIONS
# ═════════════════════════════════════════════════════════════════════════════

_tax_total_block = """  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
"""
write("neg-025-missing-tax-total.xml", valid_invoice("INV-2025-NEG-025").replace(
    _tax_total_block, "  <!-- TaxTotal (IBT-110) section omitted -->\n"),
"Missing entire cac:TaxTotal section")

_monetary_block = """  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
"""
write("neg-026-missing-monetary-total.xml", valid_invoice("INV-2025-NEG-026").replace(
    _monetary_block, "  <!-- LegalMonetaryTotal section omitted -->\n"),
"Missing entire cac:LegalMonetaryTotal section")

write("neg-027-missing-tax-subtotal.xml", valid_invoice("INV-2025-NEG-027").replace(
    """    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
""", "    <!-- TaxSubtotal omitted -->\n"),
"Missing cac:TaxSubtotal inside TaxTotal")

write("neg-028-no-invoice-lines.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-028: Invoice with zero InvoiceLines — must have at least one -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>INV-2025-NEG-028</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:TaxPointDate>2025-05-31</cbc:TaxPointDate>
  <cbc:DueDate>2025-06-15</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">0.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">0.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">0.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">0.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <!-- No InvoiceLines — invalid -->
</Invoice>""",
"Invoice with no InvoiceLines (minimum one required)")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 6 – AMOUNT / CALCULATION MISMATCHES
# ═════════════════════════════════════════════════════════════════════════════

write("neg-029-tax-total-amount-mismatch.xml", valid_invoice("INV-2025-NEG-029").replace(
    '<cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>\n    <cac:TaxSubtotal>',
    '<cbc:TaxAmount currencyID="AED">99.00</cbc:TaxAmount><!-- WRONG: 50.00 expected -->\n    <cac:TaxSubtotal>'),
"TaxTotal/TaxAmount (99.00) ≠ sum of TaxSubtotals (50.00)")

write("neg-030-tax-inclusive-mismatch.xml", valid_invoice("INV-2025-NEG-030").replace(
    '<cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>',
    '<cbc:TaxInclusiveAmount currencyID="AED">1200.00</cbc:TaxInclusiveAmount><!-- WRONG: should be 1050 -->'),
"TaxInclusiveAmount (1200) ≠ TaxExclusiveAmount + TaxAmount (1050)")

write("neg-031-payable-amount-mismatch.xml", valid_invoice("INV-2025-NEG-031").replace(
    '<cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>',
    '<cbc:PayableAmount currencyID="AED">500.00</cbc:PayableAmount><!-- WRONG: should be 1050 -->'),
"PayableAmount (500) ≠ TaxInclusiveAmount (1050)")

write("neg-032-line-extension-total-mismatch.xml", valid_invoice("INV-2025-NEG-032").replace(
    '<cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>\n    <cbc:TaxExclusiveAmount',
    '<cbc:LineExtensionAmount currencyID="AED">2000.00</cbc:LineExtensionAmount><!-- WRONG: sum of lines is 1000 -->\n    <cbc:TaxExclusiveAmount'),
"LegalMonetaryTotal/LineExtensionAmount (2000) ≠ sum of line amounts (1000)")

write("neg-033-line-amount-vs-qty-price-mismatch.xml", valid_invoice("INV-2025-NEG-033").replace(
    '    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>\n    <cac:Item>',
    '    <cbc:LineExtensionAmount currencyID="AED">999.00</cbc:LineExtensionAmount><!-- WRONG: 10×100=1000 -->\n    <cac:Item>'),
"Line LineExtensionAmount (999) ≠ Qty(10) × Price(100)")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 7 – INVALID FIELD VALUES / FORMATS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-034-invalid-date-format.xml", valid_invoice("INV-2025-NEG-034").replace(
    "<cbc:IssueDate>2025-06-01</cbc:IssueDate>",
    "<cbc:IssueDate>01/06/2025</cbc:IssueDate><!-- WRONG: must be YYYY-MM-DD -->"),
"IssueDate in wrong format (DD/MM/YYYY instead of YYYY-MM-DD)")

write("neg-035-invalid-vat-category-code.xml", valid_invoice("INV-2025-NEG-035")
    .replace("<cbc:ID>S</cbc:ID>", "<cbc:ID>X</cbc:ID><!-- INVALID VAT code -->"),
"Invalid VAT category code 'X' (not in S/AE/Z/E/O/N)")

write("neg-036-invalid-doc-type-code.xml", valid_invoice("INV-2025-NEG-036").replace(
    "<cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>",
    "<cbc:InvoiceTypeCode>999</cbc:InvoiceTypeCode><!-- INVALID: not a valid PINT AE type -->"),
"Invalid InvoiceTypeCode '999' (allowed: 380/381/389/261/480/81)")

write("neg-037-invalid-endpoint-scheme-id.xml", valid_invoice("INV-2025-NEG-037")
    .replace('schemeID="0235"', 'schemeID="9999"<!-- WRONG scheme -->'),
"Invalid schemeID '9999' on EndpointID (expected 0235)")

write("neg-038-invalid-customization-id.xml", valid_invoice("INV-2025-NEG-038").replace(
    "urn:peppol:pint:billing-1@ae-1",
    "urn:wrong:customization:id"),
"Wrong/unknown CustomizationID value")

write("neg-039-invalid-seller-country.xml", valid_invoice("INV-2025-NEG-039").replace(
    "        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>\n      </cac:PostalAddress>\n      <cac:PartyTaxScheme>",
    "        <cac:Country><cbc:IdentificationCode>GB</cbc:IdentificationCode></cac:Country><!-- WRONG: seller must be AE per BTAE-07 -->\n      </cac:PostalAddress>\n      <cac:PartyTaxScheme>"),
"Seller country code 'GB' instead of 'AE' (BTAE-07)")

write("neg-040-invalid-profile-execution-id-format.xml", valid_invoice("INV-2025-NEG-040").replace(
    "<cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>",
    "<cbc:ProfileExecutionID>STANDARD</cbc:ProfileExecutionID><!-- WRONG: must be 8-bit binary string -->"),
"ProfileExecutionID not in 8-bit binary format (BTAE-02)")

write("neg-041-wrong-vat-percent-for-s.xml", valid_invoice("INV-2025-NEG-041")
    .replace("<cbc:Percent>5</cbc:Percent>", "<cbc:Percent>15</cbc:Percent><!-- WRONG: S must be 5% in UAE -->"),
"VAT category S with wrong Percent (15 instead of 5)")

write("neg-042-negative-line-amount.xml", valid_invoice("INV-2025-NEG-042").replace(
    '    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>\n    <cac:Item>',
    '    <cbc:LineExtensionAmount currencyID="AED">-1000.00</cbc:LineExtensionAmount><!-- INVALID: negative -->\n    <cac:Item>'),
"Negative LineExtensionAmount on invoice line (use credit note instead)")

write("neg-043-zero-price-amount.xml", valid_invoice("INV-2025-NEG-043").replace(
    '      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>',
    '      <cbc:PriceAmount currencyID="AED">0.00</cbc:PriceAmount><!-- INVALID: price cannot be zero -->'),
"PriceAmount of 0.00 (ibr-co-03 violation)")

write("neg-044-non-ae-currency.xml", valid_invoice("INV-2025-NEG-044")
    .replace('currencyID="AED"', 'currencyID="USD"'),
"All amounts use USD instead of AED (AED required for UAE VAT invoices)")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 8 – BUSINESS RULE VIOLATIONS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-045-credit-note-missing-billing-reference.xml",
    valid_credit_note("CN-2025-NEG-045").replace(
        """  <cac:BillingReference>
    <cac:InvoiceDocumentReference>
      <cbc:ID>INV-2025-000</cbc:ID>
    </cac:InvoiceDocumentReference>
  </cac:BillingReference>
""", "  <!-- BillingReference (IBG-01) omitted — mandatory for all credit notes -->\n"),
"Credit note missing BillingReference/InvoiceDocumentReference (IBG-01)")

write("neg-046-credit-note-missing-discrepancy-response.xml",
    valid_credit_note("CN-2025-NEG-046").replace(
        """  <cac:DiscrepancyResponse>
    <cbc:ResponseCode>CD</cbc:ResponseCode>
  </cac:DiscrepancyResponse>
""", "  <!-- DiscrepancyResponse (BTAE-03) omitted — mandatory for credit notes -->\n"),
"Credit note missing DiscrepancyResponse (BTAE-03)")

write("neg-047-credit-note-with-tax-point-date.xml",
    valid_credit_note("CN-2025-NEG-047").replace(
        "  <cbc:CreditNoteTypeCode>381</cbc:CreditNoteTypeCode>",
        "  <cbc:TaxPointDate>2025-05-31</cbc:TaxPointDate><!-- FORBIDDEN on CN per BTAE-09 -->\n  <cbc:CreditNoteTypeCode>381</cbc:CreditNoteTypeCode>"),
"Credit note contains TaxPointDate (forbidden by BTAE-09)")

write("neg-048-margin-scheme-without-n-vat.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-048: Profit Margin Scheme transaction (bit3=1 → 00100000) but VAT=S, not N -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00100000</cbc:ProfileExecutionID>
  <cbc:ID>INV-2025-NEG-048</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:TaxPointDate>2025-05-31</cbc:TaxPointDate>
  <cbc:DueDate>2025-06-15</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID><!-- WRONG: Margin Scheme needs N, not S -->
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Margin scheme supply</cbc:Description>
      <cbc:Name>Test Item</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID><!-- WRONG: should be N -->
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
    </cac:Price>
    <cac:ItemPriceExtension>
      <cbc:Amount currencyID="AED">1050.00</cbc:Amount>
      <cac:TaxTotal><cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount></cac:TaxTotal>
    </cac:ItemPriceExtension>
  </cac:InvoiceLine>
</Invoice>""",
"Profit Margin Scheme (ProfileExecutionID=00100000) with VAT S instead of N")

write("neg-049-n-vat-without-margin-scheme.xml", valid_invoice("INV-2025-NEG-049")
    .replace("<cbc:ID>S</cbc:ID>", "<cbc:ID>N</cbc:ID><!-- N requires 00100000 txn type -->")
    .replace("<cbc:Percent>5</cbc:Percent>", "<cbc:Percent>5</cbc:Percent>"),
"VAT category N on a Standard (00000000) transaction (N requires Margin Scheme 00100000)")

write("neg-050-doc480-with-vat-s.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-050: Doc type 480 (out-of-scope invoice) with VAT S — only Z/E/O allowed -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>INV-2025-NEG-050</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:DueDate>2025-06-15</cbc:DueDate>
  <cbc:InvoiceTypeCode>480</cbc:InvoiceTypeCode><!-- out-of-scope -->
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">50.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID><!-- INVALID for doc 480: only Z/E/O allowed -->
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1050.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1050.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Out of scope supply</cbc:Description>
      <cbc:Name>Test Item</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID><!-- INVALID for doc 480 -->
        <cbc:Percent>5</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>
</Invoice>""",
"Doc type 480 with VAT S (only Z/E/O permitted for out-of-scope invoices)")

write("neg-051-e-vat-missing-exemption-code.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-051: VAT category E without TaxExemptionReasonCode — mandatory for E -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>INV-2025-NEG-051</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:InvoiceTypeCode>389</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2025-001</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer Legal Name LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="AED">1000.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>E</cbc:ID>
        <!-- TaxExemptionReasonCode deliberately omitted — mandatory for E -->
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">1000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">1000.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">1000.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="AED">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>Exempt supply</cbc:Description>
      <cbc:Name>Exempt Item</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>E</cbc:ID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="AED">100.00</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="H87">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>
</Invoice>""",
"VAT category E without TaxExemptionReasonCode (mandatory for E)")

write("neg-052-seller-trade-license-wrong-scheme.xml", valid_invoice("INV-2025-NEG-052")
    .replace('schemeAgencyID="TL">112345678900003', 'schemeAgencyID="MoF">112345678900003<!-- WRONG: must be TL per BTAE-15 -->'),
"Seller CompanyID schemeAgencyID is 'MoF' instead of 'TL' (BTAE-15)")

write("neg-053-buyer-trade-license-wrong-scheme.xml", valid_invoice("INV-2025-NEG-053")
    .replace('schemeAgencyID="TL">112345679000001', 'schemeAgencyID="CR">112345679000001<!-- WRONG: must be TL per BTAE-16 -->'),
"Buyer CompanyID schemeAgencyID is 'CR' instead of 'TL' (BTAE-16)")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 9 – DUPLICATE FIELDS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-054-duplicate-invoice-id.xml", valid_invoice("INV-2025-NEG-054").replace(
    "  <cbc:ID>INV-2025-NEG-054</cbc:ID>",
    "  <cbc:ID>INV-2025-NEG-054</cbc:ID>\n  <cbc:ID>INV-2025-NEG-054-DUPLICATE</cbc:ID><!-- INVALID: duplicate ID -->"),
"Duplicate cbc:ID elements in invoice header")

write("neg-055-duplicate-issue-date.xml", valid_invoice("INV-2025-NEG-055").replace(
    "  <cbc:IssueDate>2025-06-01</cbc:IssueDate>",
    "  <cbc:IssueDate>2025-06-01</cbc:IssueDate>\n  <cbc:IssueDate>2025-07-01</cbc:IssueDate><!-- INVALID: duplicate IssueDate -->"),
"Duplicate cbc:IssueDate elements with conflicting values")

write("neg-056-duplicate-type-code.xml", valid_invoice("INV-2025-NEG-056").replace(
    "  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>",
    "  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>\n  <cbc:InvoiceTypeCode>381</cbc:InvoiceTypeCode><!-- INVALID: duplicate TypeCode -->"),
"Duplicate cbc:InvoiceTypeCode elements (380 and 381 conflict)")

write("neg-057-duplicate-currency-code.xml", valid_invoice("INV-2025-NEG-057").replace(
    "  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>",
    "  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>\n  <cbc:DocumentCurrencyCode>USD</cbc:DocumentCurrencyCode><!-- INVALID -->"),
"Duplicate cbc:DocumentCurrencyCode elements (AED and USD)")

write("neg-058-duplicate-tax-total.xml", valid_invoice("INV-2025-NEG-058").replace(
    "  </cac:LegalMonetaryTotal>",
    """  </cac:LegalMonetaryTotal>
  <!-- Duplicate TaxTotal — invalid per schematron ibr-001 -->
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">99.00</cbc:TaxAmount>
  </cac:TaxTotal>"""),
"Two cac:TaxTotal elements with conflicting TaxAmount values")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 10 – INJECTION / SECURITY TESTS
# ═════════════════════════════════════════════════════════════════════════════

write("neg-059-script-injection-in-id.xml", valid_invoice("INV-2025-NEG-059").replace(
    "<cbc:ID>INV-2025-NEG-059</cbc:ID>",
    "<cbc:ID><![CDATA[<script>alert('XSS')</script>]]></cbc:ID>"),
"Script/XSS injection attempt in cbc:ID via CDATA")

write("neg-060-script-injection-in-name.xml", valid_invoice("INV-2025-NEG-060").replace(
    "<cbc:RegistrationName>Seller Legal Name LLC</cbc:RegistrationName>",
    "<cbc:RegistrationName>&lt;script&gt;alert('XSS')&lt;/script&gt; Seller LLC</cbc:RegistrationName>"),
"HTML/script injection in RegistrationName using XML entities")

write("neg-061-xxe-entity-injection.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE Invoice [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<!-- NEG-061: XXE entity injection attempt — processor must not resolve external entities -->
<Invoice {INV_NS}
         {COMMON}>
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
  <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
  <cbc:ID>INV-2025-NEG-061</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cbc:Note>&xxe;</cbc:Note>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Main Street</cbc:StreetName>
        <cbc:CityName>Dubai</cbc:CityName>
        <cbc:CountrySubentity>DXB</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>198765432102003</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Seller LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345678900003</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{BUYER}</cbc:EndpointID>
      <cac:PostalAddress>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Buyer LLC</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="TL">112345679000001</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="AED">0.00</cbc:TaxAmount>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AED">0.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="AED">0.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="AED">0.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="AED">0.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
</Invoice>""",
"XXE entity injection via external DTD system entity referencing /etc/passwd")


# ═════════════════════════════════════════════════════════════════════════════
#  CATEGORY 11 – MULTIPLE DOCUMENTS / WRONG ROOT ELEMENT STRUCTURE
# ═════════════════════════════════════════════════════════════════════════════

write("neg-062-two-invoices-one-file.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-062: Two Invoice elements inside a wrapper root — not a valid UBL document -->
<InvoiceCollection xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                   xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <Invoice {INV_NS}>
    <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
    <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
    <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
    <cbc:ID>INV-2025-NEG-062-A</cbc:ID>
    <cbc:IssueDate>2025-06-01</cbc:IssueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  </Invoice>
  <Invoice {INV_NS}>
    <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
    <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
    <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
    <cbc:ID>INV-2025-NEG-062-B</cbc:ID>
    <cbc:IssueDate>2025-06-01</cbc:IssueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  </Invoice>
</InvoiceCollection>""",
"Two Invoice elements in one XML file under a non-UBL wrapper root")

write("neg-063-invoice-and-credit-note-one-file.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-063: Invoice + CreditNote mixed in a single XML file — invalid UBL structure -->
<Documents xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
           xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
    <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
    <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
    <cbc:ID>INV-2025-NEG-063</cbc:ID>
    <cbc:IssueDate>2025-06-01</cbc:IssueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  </Invoice>
  <CreditNote xmlns="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2">
    <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
    <cbc:ProfileID>urn:peppol:bis:billing</cbc:ProfileID>
    <cbc:ProfileExecutionID>00000000</cbc:ProfileExecutionID>
    <cbc:ID>CN-2025-NEG-063</cbc:ID>
    <cbc:IssueDate>2025-06-01</cbc:IssueDate>
    <cbc:CreditNoteTypeCode>381</cbc:CreditNoteTypeCode>
    <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  </CreditNote>
</Documents>""",
"Invoice and CreditNote mixed in one XML file under a custom wrapper")

write("neg-064-invoice-wrong-root-element.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-064: Root element is 'Order' — not an Invoice or CreditNote -->
<Order xmlns="urn:oasis:names:specification:ubl:schema:xsd:Order-2"
       xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
       xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID>
  <cbc:ID>ORD-2025-NEG-064</cbc:ID>
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:DocumentCurrencyCode>AED</cbc:DocumentCurrencyCode>
  <cac:SellerSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{SELLER}</cbc:EndpointID>
    </cac:Party>
  </cac:SellerSupplierParty>
</Order>""",
"XML root element is 'Order' — not an Invoice or CreditNote; validator must reject")

write("neg-065-empty-xml-file.xml",
    '<?xml version="1.0" encoding="UTF-8"?>\n<!-- NEG-065: Intentionally empty XML — no root element -->',
"Empty XML file with no root element (well-formedness failure)")

write("neg-066-malformed-xml.xml",
    """<?xml version="1.0" encoding="UTF-8"?>
<!-- NEG-066: Intentionally malformed XML — unclosed tags and broken structure -->
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:ID>INV-MALFORMED
  <cbc:IssueDate>2025-06-01</cbc:IssueDate>
  <cbc:InvoiceTypeCode>380
  <UNCLOSED
""",
"Malformed XML — unclosed elements and broken syntax (not well-formed)")


# ─────────────────────────────────────────────────────────────────────────────
#  PRINT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print(f"\nGenerated {len(FILES)} negative-scenario XML files in: {OUT}\n")
print(f"{'#':<8} {'File':<55} Description")
print("-" * 130)
for i, (fname, desc) in enumerate(FILES, 1):
    print(f"{i:<8} {fname:<55} {desc}")
