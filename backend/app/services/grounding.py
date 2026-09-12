import re


_PERMISSION_QUESTION = re.compile(
    r"^\s*\b(?:can|could|may)\b.*\?|"
    r"\b(?:am|are|is)\s+(?:i|we|they|employees)?\s*"
    r"(?:allowed|permitted|entitled)\b.*\?|"
    r"\b(?:is|are)\b.*\b(?:allowed|permitted|possible|prohibited|forbidden)\b.*\?",
    re.IGNORECASE,
)
_EXPLICIT_MARKER = re.compile(
    r"\b(?:may|can|allowed|permitted|entitled|prohibited|forbidden)\b|"
    r"\b(?:cannot|can't|may not|not allowed|not permitted)\b",
    re.IGNORECASE,
)
_WORD = re.compile(r"[a-z]+")
_STOP_WORDS = {
    "a", "an", "am", "are", "be", "can", "could", "do", "does", "for",
    "how", "i", "if", "in", "is", "it", "may", "me", "my", "of", "on",
    "or", "please", "possible", "prohibited", "forbidden", "allowed", "permitted",
    "entitled", "that", "the", "they", "to", "we", "what",
    "when", "where", "which", "who", "why", "with", "would", "you", "your",
}


def _word_forms(text: str) -> set[str]:
    forms = set()
    for word in _WORD.findall(text.lower()):
        if word in _STOP_WORDS:
            continue
        forms.add(word)
        for suffix in ("ing", "ed", "es", "s"):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[: -len(suffix)]
                forms.add(stem)
                forms.add(stem + "e")
        if word.endswith("e") and len(word) > 3:
            forms.add(word[:-1])
    return forms


def is_permission_question(question: str) -> bool:
    return bool(_PERMISSION_QUESTION.search(question.strip()))


def has_explicit_support(question: str, context: str) -> bool:
    requested_terms = _word_forms(question)
    if not requested_terms:
        return False

    for sentence in re.split(r"(?<=[.!?])\s+|\n+", context):
        if not _EXPLICIT_MARKER.search(sentence):
            continue
        sentence_terms = _word_forms(sentence)
        if requested_terms <= sentence_terms:
            return True

    return False