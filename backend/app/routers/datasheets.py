from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.services.datasheets import (
    ALLOWED_SUFFIXES,
    extract_document,
    parse_inverter_document,
    parse_module_tables,
)

router = APIRouter()
MAX_SIZE = 20 * 1024 * 1024


async def read_file(file: UploadFile) -> bytes:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            400,
            "Formato no admitido. Utiliza PDF, JPG o PNG.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(400, "El archivo está vacío.")
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "El archivo supera 20 MB.")
    return data


@router.post("/module")
async def read_module(file: UploadFile = File(...)) -> dict:
    data = await read_file(file)
    try:
        document = extract_document(
            data,
            file.filename or "module.pdf",
        )
        return parse_module_tables(
            document,
            file.filename or "module.pdf",
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            422,
            "No se ha podido analizar el datasheet del módulo.",
        ) from exc


@router.post("/inverter")
async def read_inverter(file: UploadFile = File(...)) -> dict:
    data = await read_file(file)
    try:
        document = extract_document(
            data,
            file.filename or "inverter.pdf",
        )
        return parse_inverter_document(
            document,
            file.filename or "inverter.pdf",
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            422,
            "No se ha podido analizar el datasheet del inversor.",
        ) from exc
