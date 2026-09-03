from fastapi import FastAPI
from app.routes.documents import router as documents_router

app = FastAPI(
    title="HR RAG Assistant",
    description="Internal HR policy question-answering system.",
    version="1.0.0",
)

app.include_router(documents_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}