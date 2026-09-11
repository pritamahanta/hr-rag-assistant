from dataclasses import dataclass

from app.services.embedding import generate_embedding
from app.services.keyword_search import (
    keyword_index,
    rebuild_keyword_index,
)
from app.services.section_index import (
    rebuild_section_index,
    section_index,
)
from app.services.vector_store import (
    get_all_chunks,
    get_chunks_by_ids,
    search_chunks,
)


RRF_K = 60


@dataclass
class RetrievedChunk:
    text: str
    document: str
    section: str
    page: str | int
    distance: float | None
    chunk_id: str


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    top_k: int,
) -> list[str]:
    scores: dict[str, float] = {}

    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (
                1 / (RRF_K + rank)
            )

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        chunk_id
        for chunk_id, _ in ranked[:top_k]
    ]


def ensure_search_indexes() -> None:
    if keyword_index.ids and section_index.siblings:
        return

    results = get_all_chunks()

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    rebuild_keyword_index(
        texts=[
            metadata.get("search_text", document)
            for metadata, document in zip(
                metadatas,
                documents,
            )
        ],
        ids=ids,
    )

    rebuild_section_index(
        ids=ids,
        metadatas=metadatas,
    )


def retrieve_chunks(
    query: str,
    top_k: int = 8,
) -> list[RetrievedChunk]:
    ensure_search_indexes()

    candidate_k = max(top_k * 2, 10)

    query_embedding = generate_embedding(query)

    vector_results = search_chunks(
        query_embedding=query_embedding,
        top_k=candidate_k,
    )

    vector_distances = vector_results["distances"][0]
    vector_ids = vector_results["ids"][0]

    keyword_results = keyword_index.search(
        query=query,
        top_k=candidate_k,
    )

    keyword_ids = [
        chunk_id
        for chunk_id, _ in keyword_results
    ]

    ranked_ids = reciprocal_rank_fusion(
        rankings=[
            vector_ids,
            keyword_ids,
        ],
        top_k=top_k,
    )

    vector_distances_by_id = {
        chunk_id: distance
        for chunk_id, distance in zip(
            vector_ids,
            vector_distances,
        )
    }

    initial_chunks = get_chunks_by_ids(ranked_ids)

    initial_chunks_by_id = {
        chunk_id: {
            "document": document,
            "metadata": metadata,
        }
        for chunk_id, document, metadata in zip(
            initial_chunks["ids"],
            initial_chunks["documents"],
            initial_chunks["metadatas"],
        )
    }

    expanded_ids = list(ranked_ids)
    seen_ids = set(expanded_ids)

    for chunk_id in ranked_ids:
        chunk = initial_chunks_by_id.get(chunk_id)

        if not chunk:
            continue

        section = chunk["metadata"].get("section")

        sibling_ids = section_index.get_siblings(section)

        for sibling_id in sibling_ids:
            if sibling_id not in seen_ids:
                expanded_ids.append(sibling_id)
                seen_ids.add(sibling_id)

    chunks = get_chunks_by_ids(expanded_ids)

    chunks_by_id = {
        chunk_id: RetrievedChunk(
            text=document,
            document=metadata["document"],
            section=metadata["section"],
            page=metadata["page"],
            distance=vector_distances_by_id.get(chunk_id),
            chunk_id=chunk_id,
        )
        for chunk_id, document, metadata in zip(
            chunks["ids"],
            chunks["documents"],
            chunks["metadatas"],
        )
    }

    return [
        chunks_by_id[chunk_id]
        for chunk_id in expanded_ids
        if chunk_id in chunks_by_id
    ]