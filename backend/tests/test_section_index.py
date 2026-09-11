from app.services.section_index import SectionSiblingIndex


def test_section_index_returns_sibling_chunks():
    index = SectionSiblingIndex()

    index.build(
        ids=[
            "casual-1",
            "sick-1",
            "privilege-1",
            "privilege-2",
            "holiday-1",
        ],
        metadatas=[
            {"section": "Leave Policy > Leave types > Casual"},
            {"section": "Leave Policy > Leave types > Sick"},
            {"section": "Leave Policy > Leave types > Privilege"},
            {"section": "Leave Policy > Leave types > Privilege"},
            {"section": "Leave Policy > Public holidays"},
        ],
    )

    siblings = index.get_siblings(
        "Leave Policy > Leave types > Casual"
    )

    assert set(siblings) == {
        "sick-1",
        "privilege-1",
        "privilege-2",
    }


def test_section_index_does_not_mix_different_parents():
    index = SectionSiblingIndex()

    index.build(
        ids=[
            "leave-1",
            "health-1",
            "leave-2",
        ],
        metadatas=[
            {"section": "Leave Policy > Leave types > Casual"},
            {"section": "Health Policy > Benefits > Casual"},
            {"section": "Leave Policy > Leave types > Sick"},
        ],
    )

    siblings = index.get_siblings(
        "Leave Policy > Leave types > Casual"
    )

    assert siblings == ["leave-2"]


def test_section_index_returns_empty_for_top_level_section():
    index = SectionSiblingIndex()

    index.build(
        ids=["leave-1"],
        metadatas=[
            {"section": "Leave Policy"},
        ],
    )

    assert index.get_siblings("Leave Policy") == []


def test_section_index_does_not_expand_top_level_children():
    index = SectionSiblingIndex()

    index.build(
        ids=["purpose-1", "leave-types-1", "accrual-1"],
        metadatas=[
            {"section": "Leave Policy > 1. Purpose"},
            {"section": "Leave Policy > 2. Leave types"},
            {"section": "Leave Policy > 3. Accrual"},
        ],
    )

    assert index.get_siblings(
        "Leave Policy > 1. Purpose"
    ) == []