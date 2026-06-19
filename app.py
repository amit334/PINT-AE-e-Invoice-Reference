#!/usr/bin/env python3
"""
Web server for PINT AE e-Invoice Reference + XML Validator.
Serves static HTML pages and exposes /api/validate for XML validation.

Usage:
  pip install flask saxonche
  python app.py
  Open http://localhost:5000
"""

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from validate import validate
from generate_xml import generate as gen_xml
from generate_json import generate_json as gen_json, json_to_xml

STATIC_DIR   = Path(__file__).parent / "PINTAE_e-Invoice_Reference-main"
CATALOG_DIR  = Path(__file__).parent / "PINT_AE_TestCatalog_bundle" / "catalog_xml"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/catalog_xml/<path:filename>")
def catalog_xml(filename):
    return send_from_directory(CATALOG_DIR, filename, as_attachment=True)


@app.route("/api/validate", methods=["POST"])
def api_validate():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400
    if not f.filename.lower().endswith(".xml"):
        return jsonify({"error": "Only XML files are supported"}), 400

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        result = validate(tmp_path)
        return jsonify({
            "filename": f.filename,
            "doc_type": result.doc_type,
            "is_valid": result.is_valid,
            "fatal_count": result.fatal_count,
            "warning_count": result.warning_count,
            "issues": [
                {
                    "rule_id": issue.rule_id,
                    "flag": issue.flag,
                    "location": issue.location,
                    "message": issue.message,
                    "phase": issue.phase,
                }
                for issue in result.issues
            ],
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Validation error: {e}"}), 500
    finally:
        tmp_path.unlink(missing_ok=True)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    doc_type = data.get("doc_type", "380")
    vat_cats = data.get("vat_categories", ["S"])
    if not vat_cats:
        return jsonify({"error": "At least one VAT category is required"}), 400

    try:
        xml_str = gen_xml(
            doc_type=doc_type,
            vat_categories=vat_cats,
            transaction_type=data.get("transaction_type", "Standard"),
            supplier_endpoint_id=data.get("supplier_endpoint_id", ""),
            supplier_endpoint_scheme=data.get("supplier_endpoint_scheme", "0235"),
            buyer_endpoint_id=data.get("buyer_endpoint_id", ""),
            buyer_endpoint_scheme=data.get("buyer_endpoint_scheme", "0235"),
            currency=data.get("currency", "AED"),
            supplier_name=data.get("supplier_name", ""),
            buyer_name=data.get("buyer_name", ""),
            supplier_vat=data.get("supplier_vat", ""),
            buyer_vat=data.get("buyer_vat", ""),
            supplier_tl=data.get("supplier_tl", ""),
            buyer_tl=data.get("buyer_tl", ""),
            item_type=data.get("item_type", "S"),
            ftz_beneficiary_id=data.get("ftz_beneficiary_id", ""),
            agent_principal_id=data.get("agent_principal_id", ""),
        )
    except Exception as e:
        return jsonify({"error": f"Generation error: {e}"}), 500

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False,
                                     mode="w", encoding="utf-8") as tmp:
        tmp.write(xml_str)
        tmp_path = Path(tmp.name)

    try:
        result = validate(tmp_path)
        val_data = {
            "is_valid":      result.is_valid,
            "doc_type":      result.doc_type,
            "fatal_count":   result.fatal_count,
            "warning_count": result.warning_count,
            "issues": [
                {"rule_id": i.rule_id, "flag": i.flag,
                 "message": i.message, "phase": i.phase}
                for i in result.issues
            ],
        }
    except Exception as e:
        val_data = {"error": str(e), "is_valid": False}
    finally:
        tmp_path.unlink(missing_ok=True)

    cats     = "+".join(vat_cats)
    trn      = data.get("transaction_type", "Standard")
    filename = f"PINT-AE-{doc_type}-{trn}-{cats}-{date.today().strftime('%Y%m%d')}.xml"

    return jsonify({"xml": xml_str, "filename": filename, "validation": val_data})


@app.route("/api/generate-json", methods=["POST"])
def api_generate_json():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    doc_type = data.get("doc_type", "380")
    vat_cats = data.get("vat_categories", ["S"])
    if not vat_cats:
        return jsonify({"error": "At least one VAT category is required"}), 400

    try:
        json_str = gen_json(
            doc_type=doc_type,
            vat_categories=vat_cats,
            transaction_type=data.get("transaction_type", "Standard"),
            supplier_endpoint_id=data.get("supplier_endpoint_id", ""),
            supplier_endpoint_scheme=data.get("supplier_endpoint_scheme", "0235"),
            buyer_endpoint_id=data.get("buyer_endpoint_id", ""),
            buyer_endpoint_scheme=data.get("buyer_endpoint_scheme", "0235"),
            currency=data.get("currency", "AED"),
            supplier_name=data.get("supplier_name", ""),
            buyer_name=data.get("buyer_name", ""),
            supplier_vat=data.get("supplier_vat", ""),
            buyer_vat=data.get("buyer_vat", ""),
            supplier_tl=data.get("supplier_tl", ""),
            buyer_tl=data.get("buyer_tl", ""),
            item_type=data.get("item_type", "S"),
            ftz_beneficiary_id=data.get("ftz_beneficiary_id", ""),
            agent_principal_id=data.get("agent_principal_id", ""),
        )
    except Exception as e:
        return jsonify({"error": f"Generation error: {e}"}), 500

    # Validate by converting JSON → XML → schematron
    try:
        xml_str = json_to_xml(json_str)
    except Exception as e:
        return jsonify({"json": json_str, "filename": _json_filename(data),
                        "validation": {"error": f"Conversion error: {e}", "is_valid": False}}), 200

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False,
                                     mode="w", encoding="utf-8") as tmp:
        tmp.write(xml_str)
        tmp_path = Path(tmp.name)

    try:
        result = validate(tmp_path)
        val_data = {
            "is_valid":      result.is_valid,
            "doc_type":      result.doc_type,
            "fatal_count":   result.fatal_count,
            "warning_count": result.warning_count,
            "issues": [{"rule_id": i.rule_id, "flag": i.flag,
                        "message": i.message, "phase": i.phase}
                       for i in result.issues],
        }
    except Exception as e:
        val_data = {"error": str(e), "is_valid": False}
    finally:
        tmp_path.unlink(missing_ok=True)

    return jsonify({"json": json_str, "filename": _json_filename(data), "validation": val_data})


@app.route("/api/validate-json", methods=["POST"])
def api_validate_json():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400
    if not f.filename.lower().endswith(".json"):
        return jsonify({"error": "Only JSON files are supported"}), 400

    try:
        json_str = f.read().decode("utf-8")
        json.loads(json_str)  # validate it parses
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    try:
        xml_str = json_to_xml(json_str)
    except Exception as e:
        return jsonify({"error": f"JSON→XML conversion failed: {e}"}), 422

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False,
                                     mode="w", encoding="utf-8") as tmp:
        tmp.write(xml_str)
        tmp_path = Path(tmp.name)

    try:
        result = validate(tmp_path)
        return jsonify({
            "filename":      f.filename,
            "doc_type":      result.doc_type,
            "is_valid":      result.is_valid,
            "fatal_count":   result.fatal_count,
            "warning_count": result.warning_count,
            "issues": [{"rule_id": i.rule_id, "flag": i.flag,
                        "location": i.location, "message": i.message, "phase": i.phase}
                       for i in result.issues],
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Validation error: {e}"}), 500
    finally:
        tmp_path.unlink(missing_ok=True)


def _json_filename(data: dict) -> str:
    cats = "+".join(data.get("vat_categories", ["X"]))
    return f"PINT-AE-{data.get('doc_type','380')}-{data.get('transaction_type','Standard')}-{cats}-{date.today().strftime('%Y%m%d')}.json"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
