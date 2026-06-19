#!/usr/bin/env python3
"""
PINT AE (UAE) UBL Invoice/CreditNote Schematron Validator
Validates UBL XML against PINT AE Billing 1.0.4 and Self-Billing 1.0.4 (ae-1) rules.
"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

try:
    from saxonche import PySaxonProcessor
except ImportError:
    print("ERROR: saxonche not installed. Run: pip install saxonche", file=sys.stderr)
    sys.exit(1)

BILLING_BASE_DIR    = Path(__file__).parent / "pint-ae-resources-dev"
SB_BASE_DIR         = Path(__file__).parent / "pint-ae-sb-resources-dev"

BILLING_URN     = "urn:peppol:pint:billing-1@ae-1"
SELF_BILLING_URN = "urn:peppol:pint:selfbilling-1@ae-1"

SVRL_NS = "http://purl.oclc.org/dsdl/svrl"

# Maps XML root element tag → (trn subfolder, base label)
DOC_TYPE_MAP = {
    "Invoice":                                                              ("trn-invoice",    "Invoice"),
    "{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice":     ("trn-invoice",    "Invoice"),
    "CreditNote":                                                           ("trn-creditnote", "CreditNote"),
    "{urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2}CreditNote": ("trn-creditnote", "CreditNote"),
}

PHASE_FILES = [
    "PINT-UBL-validation-preprocessed.xslt",
    "PINT-jurisdiction-aligned-rules.xslt",
]

PHASE_LABELS = [
    "PINT UBL Core Rules",
    "UAE Jurisdiction-Aligned Rules",
]


@dataclass
class ValidationIssue:
    rule_id: str
    flag: Literal["fatal", "warning"]
    location: str
    message: str
    phase: str


@dataclass
class ValidationResult:
    xml_file: str
    doc_type: str
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def fatal_count(self) -> int:
        return sum(1 for i in self.issues if i.flag == "fatal")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.flag == "warning")


def detect_doc_type(xml_path: Path) -> tuple[str, Path, str]:
    """Return (trn_subfolder, base_dir, doc_type_label) for the given XML file.

    Checks the root element tag for Invoice vs CreditNote, then reads
    CustomizationID to distinguish PINT AE Billing from Self-Billing resources.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    mapping = DOC_TYPE_MAP.get(root.tag)
    if mapping is None:
        raise ValueError(
            f"Unrecognised root element '{root.tag}'. "
            "Expected UBL Invoice or CreditNote."
        )
    trn, base_label = mapping

    # Read CustomizationID (first child with that local name, any namespace)
    cust_id = ""
    for child in root:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == "CustomizationID":
            cust_id = (child.text or "").strip()
            break

    if cust_id.startswith(SELF_BILLING_URN):
        base_dir = SB_BASE_DIR
        label = f"Self-Billing {base_label}"
    else:
        base_dir = BILLING_BASE_DIR
        label = base_label

    return trn, base_dir, label


def run_xslt(proc: "PySaxonProcessor", xslt_path: Path, xml_path: Path) -> ET.Element:
    """Apply one XSLT 2.0 stylesheet and return the SVRL root element."""
    xslt_proc = proc.new_xslt30_processor()
    xslt_proc.set_parameter("fileNameParameter", proc.make_string_value(str(xml_path)))
    xslt_proc.set_parameter("fileDirParameter", proc.make_string_value(str(xml_path.parent)))
    executable = xslt_proc.compile_stylesheet(stylesheet_file=str(xslt_path))
    svrl_str = executable.transform_to_string(source_file=str(xml_path))
    if not svrl_str:
        raise RuntimeError(f"XSLT produced no output for {xslt_path.name}")
    return ET.fromstring(svrl_str)


def parse_svrl(svrl_root: ET.Element, phase_label: str) -> list[ValidationIssue]:
    """Extract failed-assert and successful-report elements from SVRL."""
    issues: list[ValidationIssue] = []
    for tag in ("failed-assert", "successful-report"):
        for el in svrl_root.iter(f"{{{SVRL_NS}}}{tag}"):
            flag = el.get("flag", "fatal")
            rule_id = el.get("id", "unknown")
            location = el.get("location", "")
            text_el = el.find(f"{{{SVRL_NS}}}text")
            message = (text_el.text or "").strip() if text_el is not None else ""
            issues.append(ValidationIssue(
                rule_id=rule_id,
                flag=flag,
                location=location,
                message=message,
                phase=phase_label,
            ))
    return issues


def validate(xml_path: Path) -> ValidationResult:
    """Run full PINT AE validation against the given UBL XML file."""
    xml_path = xml_path.resolve()
    if not xml_path.exists():
        raise FileNotFoundError(f"File not found: {xml_path}")

    trn, base_dir, doc_type_label = detect_doc_type(xml_path)
    schematron_dir = base_dir / trn / "schematron"

    all_issues: list[ValidationIssue] = []

    with PySaxonProcessor(license=False) as proc:
        for xslt_file, label in zip(PHASE_FILES, PHASE_LABELS):
            xslt_path = schematron_dir / xslt_file
            svrl_root = run_xslt(proc, xslt_path, xml_path)
            all_issues.extend(parse_svrl(svrl_root, label))

    is_valid = not any(i.flag == "fatal" for i in all_issues)
    return ValidationResult(
        xml_file=str(xml_path),
        doc_type=doc_type_label,
        is_valid=is_valid,
        issues=all_issues,
    )


# ---------------------------------------------------------------------------
# CLI output helpers
# ---------------------------------------------------------------------------

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"

def _color(text: str, code: str, use_color: bool) -> str:
    return f"{code}{text}{RESET}" if use_color else text


def print_result(result: ValidationResult, use_color: bool = True, verbose: bool = False) -> None:
    c = lambda t, code: _color(t, code, use_color)

    print()
    print(c("=" * 60, BOLD))
    print(c(f"  PINT AE Validation Report", BOLD))
    print(c("=" * 60, BOLD))
    print(f"  File     : {result.xml_file}")
    print(f"  Type     : {result.doc_type}")

    if result.is_valid:
        status = c("  VALID", GREEN + BOLD)
        if result.warning_count:
            status += c(f"  ({result.warning_count} warning(s))", YELLOW)
    else:
        status = c(f"  INVALID  ({result.fatal_count} fatal error(s)", RED + BOLD)
        if result.warning_count:
            status += c(f", {result.warning_count} warning(s)", YELLOW)
        status += c(")", RED + BOLD)

    print(f"  Status   :{status}")
    print(c("-" * 60, DIM))

    if not result.issues:
        print(c("  No issues found.", GREEN))
    else:
        grouped: dict[str, list[ValidationIssue]] = {}
        for issue in result.issues:
            grouped.setdefault(issue.phase, []).append(issue)

        for phase, issues in grouped.items():
            print()
            print(c(f"  Phase: {phase}", CYAN + BOLD))
            for issue in issues:
                if issue.flag == "fatal":
                    marker = c("[FATAL]  ", RED + BOLD)
                else:
                    marker = c("[WARNING]", YELLOW + BOLD)

                print(f"    {marker} {c(issue.rule_id, BOLD)}")
                print(f"             {issue.message}")
                if verbose and issue.location:
                    print(c(f"             Location: {issue.location}", DIM))

    print()
    print(c("=" * 60, BOLD))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a UBL Invoice or CreditNote against PINT AE Billing/Self-Billing (UAE) schematron rules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate.py invoice.xml
  python validate.py "path/to/Standard tax invoice.xml"
  python validate.py invoice.xml --verbose
  python validate.py invoice.xml --no-color
""",
    )
    parser.add_argument("xml_file", help="Path to UBL Invoice or CreditNote XML file")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show XPath location for each issue")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Only print VALID/INVALID with issue counts")

    args = parser.parse_args()

    try:
        result = validate(Path(args.xml_file))
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR during validation: {e}", file=sys.stderr)
        return 2

    use_color = not args.no_color and sys.stdout.isatty()

    if args.quiet:
        if result.is_valid:
            msg = f"VALID — {result.xml_file}"
            if result.warning_count:
                msg += f" ({result.warning_count} warning(s))"
        else:
            msg = (f"INVALID — {result.xml_file} "
                   f"({result.fatal_count} fatal, {result.warning_count} warning(s))")
        print(msg)
    else:
        print_result(result, use_color=use_color, verbose=args.verbose)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
