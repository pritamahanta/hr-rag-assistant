import os

import chromadb
from dotenv import load_dotenv

load_dotenv(".env")

COLLECTION_NAME = "hr_policies"

client = chromadb.CloudClient(
    api_key=os.environ["CHROMA_API_KEY"],
    tenant=os.environ["CHROMA_TENANT"],
    database=os.environ["CHROMA_DATABASE"],
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    configuration={"hnsw": {"space": "cosine"}},
)

def add_chunks(
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str],
    target_collection=None,
) -> None:
    target = target_collection or collection

    target.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )


def search_chunks(
    query_embedding: list[float],
    top_k: int = 5,
    target_collection=None,
) -> dict:
    target = target_collection or collection

    return target.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )


def get_all_chunks(
    target_collection=None,
) -> dict:
    target = target_collection or collection

    return target.get(
        include=["documents", "metadatas"],
    )


def get_chunks_by_ids(
    ids: list[str],
    target_collection=None,
) -> dict:
    target = target_collection or collection

    if not ids:
        return {
            "documents": [],
            "metadatas": [],
            "ids": [],
        }

    return target.get(
        ids=ids,
        include=["documents", "metadatas"],
    )


def delete_document(
    document: str,
    target_collection=None,
) -> int:
    target = target_collection or collection

    results = target.get(
        where={"document": document},
    )

    ids = results.get("ids", [])

    if ids:
        target.delete(ids=ids)

    return len(ids)


def replace_document(
    document: str,
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str],
    target_collection=None,
) -> None:
    target = target_collection or collection

    delete_document(
        document,
        target_collection=target,
    )

    target.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )