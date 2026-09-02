from fastapi import FastAPI 

app = FastAPI(
    title = "HR RAG Assistant",
    description = "Internal HR policy question-answering system.",
    version = "1.0.0",
)

@app.get("/health")

def health_check():
    return {"status" : "ok"} 