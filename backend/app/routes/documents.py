import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import require_admin
from app.services.ingestion import ingest_document
from app.services.keyword_search import rebuild_keyword_index
from app.services.storage import delete_file, list_files, upload_file
from app.services.vector_store import delete_document, get_all_chunks

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/")
def list_documents():
    documents = [
        filename
        for filename in list_files()
        if Path(filename).suffix.lower() in ALLOWED_EXTENSIONS
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

    with tempfile.NamedTemporaryFile(
        suffix=extension,
        delete=False,
    ) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        upload_file(
            file_path=str(temp_path),
            storage_path=filename,
        )

        chunks_indexed = ingest_document(
            temp_path,
            document_name=filename,
        )
    except Exception as exc:
        try:
            delete_file(filename)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed. Please try again.",
        ) from exc

    finally:
        temp_path.unlink(missing_ok=True)

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

    try:
        delete_file(filename)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document. Please try again.",
        ) from exc

    chunks_deleted = delete_document(filename)

    results = get_all_chunks()

    rebuild_keyword_index(
        texts=results.get("documents", []),
        ids=results.get("ids", []),
    )

    if chunks_deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "message": "Document deleted successfully.",
        "filename": filename,
        "chunks_deleted": chunks_deleted,
    }