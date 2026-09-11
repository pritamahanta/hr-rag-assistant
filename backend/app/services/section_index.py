class SectionSiblingIndex:
    def __init__(self):
        # parent section -> section -> chunk IDs
        self.siblings: dict[str, dict[str, list[str]]] = {}

    def build(
        self,
        ids: list[str],
        metadatas: list[dict],
    ) -> None:
        self.siblings = {}

        for chunk_id, metadata in zip(ids, metadatas):
            section = metadata.get("section") or ""

            if " > " not in section:
                continue

            parent = section.rsplit(" > ", 1)[0]

            self.siblings.setdefault(parent, {})
            self.siblings[parent].setdefault(section, [])
            self.siblings[parent][section].append(chunk_id)

    def get_siblings(
        self,
        section: str | None,
    ) -> list[str]:
        if not section or " > " not in section:
            return []

        parent = section.rsplit(" > ", 1)[0]

        sibling_sections = self.siblings.get(parent, {})

        sibling_ids = []

        for sibling_section, chunk_ids in sibling_sections.items():
            if sibling_section != section:
                sibling_ids.extend(chunk_ids)

        return sibling_ids


section_index = SectionSiblingIndex()


def rebuild_section_index(
    ids: list[str],
    metadatas: list[dict],
) -> None:
    section_index.build(
        ids=ids,
        metadatas=metadatas,
    )