from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.services.ingestion import ingest_document
from app.services.vector_store import delete_document

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("data/documents")
ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):  
    
    if not file.filename:
        raise HTTPException (
            status_code = 400,
            detail = "Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed types: .md, .txt, .pdf",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / file.filename

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
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
        "filename": file.filename,
        "chunks_indexed": chunks_indexed,
    }



@router.delete("/{filename}")
def delete_uploaded_document(filename: str):

    file_path = UPLOAD_DIR / filename
    file_exists = file_path.exists()

    chunks_deleted = delete_document(filename)

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