import chromadb

CHROMA_PATH = "data/chroma"

client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_or_create_collection( name="hr_policies" )

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