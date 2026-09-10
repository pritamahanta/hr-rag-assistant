from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.documents import router as documents_router
from app.routes.query import router as query_router

app = FastAPI(
    title="HR RAG Assistant",
    description="Internal HR policy question-answering system.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(query_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}