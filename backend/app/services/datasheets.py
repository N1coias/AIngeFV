from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Iterable

import fitz
import pdfplumber
import pytesseract
from PIL import Image


ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("−", "-")).strip()


def extract_document(content: bytes, filename: str) -> dict:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Formato no admitido. Utiliza PDF, JPG o PNG.")

    if suffix in {".jpg", ".jpeg", ".png"}:
        image = Image.open(io.BytesIO(content)).convert("RGB")
        text = pytesseract.image_to_string(image, lang="eng")
        return {
            "text": text,
            "tables": [],
            "method": "ocr-image",
            "sha256": sha256_bytes(content),
        }

    text_parts: list[str] = []
    tables: list[list[list[str | None]]] = []

    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            for page in document:
                text_parts.append(page.get_text("text"))
    except Exception as exc:
        raise ValueError("El archivo PDF no es válido o está dañado.") from exc

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                tables.extend(page.extract_tables() or [])
    except Exception:
        pass

    text = "\n".join(text_parts).strip()
    method = "pdf-text-and-tables"

    if len(text) < 100:
        ocr_parts: list[str] = []
        with fitz.open(stream=content, filetype="pdf") as document:
            for page in list(document)[:4]:
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(2.4, 2.4),
                    alpha=False,
                )
                image = Image.frombytes(
                    "RGB",
                    [pixmap.width, pixmap.height],
                    pixmap.samples,
                )
                ocr_parts.append(
                    pytesseract.image_to_string(image, lang="eng")
                )
        text = "\n".join(ocr_parts)
        method = "ocr-pdf"

    if len(text.strip()) < 30 and not tables:
        raise ValueError(
            "No se ha podido obtener texto ni tablas del documento."
        )

    return {
        "text": text,
        "tables": tables,
        "method": method,
        "sha256": sha256_bytes(content),
    }


def _numbers(value: str | None) -> list[float]:
    if not value:
        return []
    return [
        float(item.replace(",", "."))
        for item in re.findall(
            r"-?\d+(?:[.,]\d+)?",
            value.replace("−", "-"),
        )
    ]


def _row_numbers(row: list[str | None]) -> list[float]:
    values: list[float] = []
    for cell in row[1:]:
        values.extend(_numbers(cell))
    return values


def _find_row(
    table: list[list[str | None]],
    labels: Iterable[str],
) -> list[str | None] | None:
    for row in table:
        if not row:
            continue
        heading = _normalise_text(" ".join(
            str(cell or "") for cell in row[:2]
        )).lower()
        if any(label in heading for label in labels):
            return row
    return None


def _line_values(
    text: str,
    labels: Iterable[str],
    minimum: float,
    maximum: float,
) -> list[float]:
    for line in text.splitlines():
        normalised = _normalise_text(line)
        lower = normalised.lower()
        if any(label in lower for label in labels):
            values = [
                number
                for number in _numbers(normalised)
                if minimum <= number <= maximum
            ]
            if values:
                return values
    return []


def _fit_count(
    values: list[float],
    count: int,
    minimum: float,
    maximum: float,
) -> list[float]:
    filtered = [
        value for value in values
        if minimum <= value <= maximum
    ]
    if len(filtered) >= count:
        return filtered[-count:]
    return filtered


def _coefficient(
    text: str,
    labels: Iterable[str],
) -> float | None:
    flattened = _normalise_text(text)
    for label in labels:
        match = re.search(
            rf"{label}[^-\d]{{0,80}}(-?\d+(?:[.,]\d+)?)",
            flattened,
            re.I,
        )
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def _detect_module_identity(text: str, filename: str) -> tuple[str, str]:
    upper = text.upper()
    manufacturers = [
        "JA SOLAR",
        "JINKO",
        "LONGI",
        "TRINA",
        "CANADIAN SOLAR",
        "ASTRONERGY",
        "AIKO",
        "RISEN",
    ]
    manufacturer = next(
        (name.title() for name in manufacturers if name in upper),
        "",
    )

    patterns = [
        r"\bJAM[A-Z0-9./-]{5,}\b",
        r"\bJKM[A-Z0-9./-]{5,}\b",
        r"\bLR\d[A-Z0-9./-]{5,}\b",
        r"\bTSM-[A-Z0-9./-]{5,}\b",
        r"\bCS\d[A-Z0-9./-]{5,}\b",
    ]
    family = ""
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            family = match.group(0)
            break

    return manufacturer, family or Path(filename).stem


def parse_module_tables(document: dict, filename: str) -> dict:
    text = document["text"]
    powers: list[float] = []
    vocs: list[float] = []
    vmps: list[float] = []
    iscs: list[float] = []
    imps: list[float] = []

    for table in document["tables"]:
        power_row = _find_row(
            table,
            ("maximum power", "max power", "pmax"),
        )
        voc_row = _find_row(
            table,
            ("open circuit voltage", "voc"),
        )
        vmp_row = _find_row(
            table,
            ("maximum power voltage", "vmp", "vmpp"),
        )
        isc_row = _find_row(
            table,
            ("short circuit current", "isc"),
        )
        imp_row = _find_row(
            table,
            ("maximum power current", "imp", "impp"),
        )

        if power_row:
            powers = _row_numbers(power_row)
        if voc_row:
            vocs = _row_numbers(voc_row)
        if vmp_row:
            vmps = _row_numbers(vmp_row)
        if isc_row:
            iscs = _row_numbers(isc_row)
        if imp_row:
            imps = _row_numbers(imp_row)

        if all((powers, vocs, vmps, iscs, imps)):
            break

    if not powers:
        powers = _line_values(
            text,
            ("maximum power", "pmax"),
            200,
            1000,
        )
    if not vocs:
        vocs = _line_values(
            text,
            ("open circuit voltage", "voc"),
            10,
            100,
        )
    if not vmps:
        vmps = _line_values(
            text,
            ("maximum power voltage", "vmp", "vmpp"),
            10,
            100,
        )
    if not iscs:
        iscs = _line_values(
            text,
            ("short circuit current", "isc"),
            1,
            40,
        )
    if not imps:
        imps = _line_values(
            text,
            ("maximum power current", "imp", "impp"),
            1,
            40,
        )

    powers = [
        value for value in powers
        if 200 <= value <= 1000
    ]
    count = len(powers)

    variants: list[dict] = []
    if count:
        vocs = _fit_count(vocs, count, 10, 100)
        vmps = _fit_count(vmps, count, 10, 100)
        iscs = _fit_count(iscs, count, 1, 40)
        imps = _fit_count(imps, count, 1, 40)

        if min(len(vocs), len(vmps), len(iscs), len(imps)) >= count:
            manufacturer, family = _detect_module_identity(
                text,
                filename,
            )
            seen: set[tuple] = set()
            for index in range(count):
                key = (
                    powers[index],
                    vocs[index],
                    vmps[index],
                    iscs[index],
                    imps[index],
                )
                if key in seen:
                    continue
                seen.add(key)
                variants.append({
                    "manufacturer": manufacturer,
                    "family": family,
                    "model": f"{family}-{int(powers[index])}",
                    "pmax_w": powers[index],
                    "voc_v": vocs[index],
                    "vmp_v": vmps[index],
                    "isc_a": iscs[index],
                    "imp_a": imps[index],
                })

    beta_voc = _coefficient(
        text,
        (
            r"temperature coefficient of voc",
            r"β.?voc",
        ),
    )
    beta_vmp = _coefficient(
        text,
        (
            r"temperature coefficient of vmp",
            r"β.?vmp",
        ),
    )

    warnings = ["Confirma todos los valores antes de guardarlos."]
    if not variants:
        warnings.append(
            "No se ha reconstruido una tabla eléctrica completa."
        )
    if beta_voc is None:
        warnings.append("No se ha localizado βVoc.")
    if beta_vmp is None:
        warnings.append(
            "No se ha localizado βVmp; introdúcelo manualmente."
        )

    confidence = 0.25
    if variants:
        confidence += 0.45
    if beta_voc is not None:
        confidence += 0.15
    if beta_vmp is not None:
        confidence += 0.15

    return {
        "document_type": "module",
        "source_filename": filename,
        "datasheet_sha256": document["sha256"],
        "variants": variants,
        "beta_voc_pct_c": beta_voc,
        "beta_vmp_pct_c": beta_vmp,
        "method": document["method"],
        "confidence": min(confidence, 1.0),
        "warnings": warnings,
    }


def _first_number(
    text: str,
    patterns: Iterable[str],
    minimum: float,
    maximum: float,
) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = float(match.group(1).replace(",", "."))
            if minimum <= value <= maximum:
                return value
    return None


def _power_w(text: str) -> float | None:
    patterns = [
        (
            r"(?:rated ac active power|rated output power|"
            r"nominal ac power)[^\d]{0,50}"
            r"(\d+(?:[.,]\d+)?)\s*(kw|w)\b"
        ),
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = float(match.group(1).replace(",", "."))
            unit = match.group(2).lower()
            return value * 1000.0 if unit == "kw" else value
    return None


def _detect_inverter_identity(
    text: str,
    filename: str,
) -> tuple[str, str]:
    upper = text.upper()
    manufacturers = [
        "HUAWEI",
        "SUNGROW",
        "INGETEAM",
        "SMA",
        "FRONIUS",
        "GOODWE",
        "SOLIS",
    ]
    manufacturer = next(
        (name.title() for name in manufacturers if name in upper),
        "",
    )

    patterns = [
        r"\bSUN2000-[A-Z0-9.-]+\b",
        r"\bSG\d+[A-Z0-9-]*\b",
        r"\bINGECON SUN [A-Z0-9 -]+\b",
        r"\bSTP \d+[A-Z0-9-]*\b",
    ]
    model = ""
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            model = _normalise_text(match.group(0))
            break

    return manufacturer, model or Path(filename).stem


def parse_inverter_document(document: dict, filename: str) -> dict:
    text = _normalise_text(document["text"])
    manufacturer, model = _detect_inverter_identity(
        text,
        filename,
    )

    range_match = re.search(
        r"(?:mppt|mpp).*?(?:range|operating).*?"
        r"(\d{2,4})\s*(?:v)?\s*(?:-|–|~|to)\s*(\d{2,4})",
        text,
        re.I,
    )

    data = {
        "manufacturer": manufacturer,
        "model": model,
        "pac_w": _power_w(text),
        "max_dc_voltage_v": _first_number(
            text,
            (
                r"maximum input voltage[^\d]{0,40}(\d{3,4})",
                r"max\.?\s*dc voltage[^\d]{0,40}(\d{3,4})",
            ),
            100,
            2000,
        ),
        "mppt_min_v": (
            float(range_match.group(1))
            if range_match else None
        ),
        "mppt_max_v": (
            float(range_match.group(2))
            if range_match else None
        ),
        "mppt_count": _first_number(
            text,
            (
                r"number of (?:mpp trackers|mppts)"
                r"[^\d]{0,30}(\d{1,2})",
            ),
            1,
            50,
        ),
        "inputs_per_mppt": _first_number(
            text,
            (
                r"(?:inputs per mppt|"
                r"max\.? number of inputs per mppt)"
                r"[^\d]{0,30}(\d{1,2})",
            ),
            1,
            30,
        ),
        "max_current_per_mppt_a": _first_number(
            text,
            (
                r"max(?:imum)?\.? current per mppt"
                r"[^\d]{0,40}(\d{1,3}(?:[.,]\d+)?)",
            ),
            1,
            500,
        ),
        "max_current_per_string_a": _first_number(
            text,
            (
                r"max(?:imum)?\.? current per (?:input|string)"
                r"[^\d]{0,40}(\d{1,3}(?:[.,]\d+)?)",
            ),
            1,
            100,
        ),
        "max_short_circuit_per_mppt_a": _first_number(
            text,
            (
                r"max(?:imum)?\.? short circuit current per mppt"
                r"[^\d]{0,40}(\d{1,3}(?:[.,]\d+)?)",
            ),
            1,
            1000,
        ),
    }

    missing = [
        key for key, value in data.items()
        if key not in {"manufacturer", "model"}
        and value is None
    ]
    found_count = len(data) - 2 - len(missing)
    confidence = min(0.25 + found_count * 0.1, 0.95)

    return {
        "document_type": "inverter",
        "source_filename": filename,
        "datasheet_sha256": document["sha256"],
        "inverter": data,
        "method": document["method"],
        "confidence": confidence,
        "warnings": [
            "Confirma todos los valores antes de guardarlos.",
            *(
                [f"Faltan campos: {', '.join(missing)}"]
                if missing else []
            ),
        ],
    }
