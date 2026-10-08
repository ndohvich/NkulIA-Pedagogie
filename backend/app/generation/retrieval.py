"""Recherche pédagogique embarquée (« RAG sans serveur externe »).

Principe retenu pour le MVP (ADR-0005) : pas de base vectorielle ni de
modèle d'embeddings à télécharger — contraire à l'offline-first sur un
poste à connexion instable. On classe les unités d'enseignement déjà
importées par recouvrement lexical (indice de Jaccard sur des mots
normalisés). Suffisant pour retrouver des unités voisines ; remplaçable
plus tard (phase 5) derrière la même fonction `related_units`.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

_STOPWORDS = frozenset(
    [
        "le",
        "la",
        "les",
        "un",
        "une",
        "des",
        "de",
        "du",
        "d",
        "l",
        "et",
        "ou",
        "en",
        "au",
        "aux",
        "a",
        "à",
        "dans",
        "sur",
        "pour",
        "par",
        "avec",
        "sans",
        "son",
        "sa",
        "ses",
        "ce",
        "cette",
        "ces",
        "qui",
        "que",
        "quoi",
        "est",
        "sont",
        "etre",
        "avoir",
        "plus",
        "moins",
        "comme",
        "leur",
        "leurs",
    ]
)


def tokenize(text: str) -> frozenset[str]:
    """Mots en minuscules, sans accents ni mots vides, 2 lettres minimum."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z0-9]+", ascii_text)
    return frozenset(word for word in words if len(word) >= 2 and word not in _STOPWORDS)


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def related_units(
    query: str, candidates: Iterable[tuple[int, str]], limit: int = 3
) -> list[tuple[int, float]]:
    """Renvoie `(id, score)` des `limit` candidats les plus proches, score > 0 seulement."""
    query_tokens = tokenize(query)
    scored = [(unit_id, jaccard(query_tokens, tokenize(text))) for unit_id, text in candidates]
    ranked = sorted((item for item in scored if item[1] > 0), key=lambda item: (-item[1], item[0]))
    return ranked[:limit]
