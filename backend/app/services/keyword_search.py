import re

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


class KeywordIndex:
    def __init__(self):
        self.ids: list[str] = []
        self.texts: list[str] = []
        self.bm25: BM25Okapi | None = None

    def build(
        self,
        texts: list[str],
        ids: list[str],
    ) -> None:
        if len(texts) != len(ids):
            raise ValueError("texts and ids must have the same length.")

        self.texts = texts
        self.ids = ids

        tokenized_texts = [
            tokenize(text)
            for text in texts
        ]

        self.bm25 = (
            BM25Okapi(tokenized_texts)
            if tokenized_texts
            else None
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        if not query.strip() or not self.ids or self.bm25 is None:
            return []

        query_tokens = tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(self.ids, scores),
            key=lambda item: item[1],
            reverse=True,
        )

        return ranked[:top_k]


keyword_index = KeywordIndex()


def rebuild_keyword_index(
    texts: list[str],
    ids: list[str],
) -> None:
    keyword_index.build(
        texts=texts,
        ids=ids,
    )