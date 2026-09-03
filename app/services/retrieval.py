from dataclasses import dataclass

from app.services.embedding import generate_embedding
from app.services.vector_store import search_chunks


@dataclass
class RetrievedChunk:
    text: str
    document: str
    section: str
    page: str | int
    distance: float


def retrieve_chunks(
    query: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    query_embedding = generate_embedding(query)

    results = search_chunks(
        query_embedding=query_embedding,
        top_k=top_k,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        chunks.append(
            RetrievedChunk(
                text=document,
                document=metadata["document"],
                section=metadata["section"],
                page=metadata["page"],
                distance=distance,
            )
        )

    return chunks