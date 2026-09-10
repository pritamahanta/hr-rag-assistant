from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends

from app.services.ingestion import ingest_document
from app.services.keyword_search import rebuild_keyword_index
from app.services.vector_store import (
    delete_document,
    get_all_chunks,
)
from app.core.auth import require_admin

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("data/documents")
ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/")
def list_documents():
    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents = [
        path.name
        for path in UPLOAD_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    return {
        "documents": sorted(documents),
    }


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    _: str = Depends(require_admin),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed types: .md, .txt, .pdf",
        )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = UPLOAD_DIR / filename

    content = file.file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file is too large. Maximum size is 10 MB.",
        )

    file_path.write_bytes(content)

    try:
        chunks_indexed = ingest_document(file_path)
    except Exception as exc:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {exc}",
        ) from exc

    return {
        "message": "Document uploaded and indexed successfully.",
        "filename": filename,
        "chunks_indexed": chunks_indexed,
    }


@router.delete("/{filename}")
def delete_uploaded_document(
    filename: str,
     _: str = Depends(require_admin),
):
    filename = Path(filename).name
    file_path = UPLOAD_DIR / filename

    file_exists = file_path.exists()

    chunks_deleted = delete_document(filename)

    results = get_all_chunks()

    rebuild_keyword_index(
        texts=results.get("documents", []),
        ids=results.get("ids", []),
    )

    if file_exists:
        try:
            file_path.unlink()
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document file: {exc}",
            ) from exc

    if chunks_deleted == 0 and not file_exists:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "message": "Document deleted successfully.",
        "filename": filename,
        "chunks_deleted": chunks_deleted,
    }