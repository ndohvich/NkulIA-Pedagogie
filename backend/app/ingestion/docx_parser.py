"""Parseur des documents pédagogiques réels (issue #9).

Écrit et validé contre le corpus réel du Lycée Technique d'Ébolowa
(voir backend/tests/fixtures/ et tests/unit/test_docx_parser.py), pas
contre des exemples imaginés à l'avance — voir les notes de conception
ci-dessous, tirées de l'inspection ligne par ligne de vrais fichiers.

Trois irrégularités réelles à connaître avant de modifier ce fichier :

1. Le vocabulaire de l'EN-TÊTE (« Chapitres », « Leçons ») ne garantit
   pas le vocabulaire réellement écrit DANS les cellules — un document
   technique (Niveau 1) dont l'en-tête dit « Chapitres » contient
   malgré tout des cellules qui commencent par « UA ». Le
   `track_schema` du document se lit donc sur l'EN-TÊTE (voir
   track_schema.py), jamais en devinant à partir du contenu des cellules.
2. Une cellule d'Unité d'Enseignement / Leçon peut contenir PLUSIEURS
   unités, séparées par un saut de ligne à l'intérieur de la cellule.
3. Certaines lignes ne sont pas du contenu pédagogique (« ÉVALUATION
   DE FIN DE TRIMESTRE », « REMEDIATION ») : leur cellule d'Unité
   d'Apprentissage / Chapitre ne correspond à aucun motif « UA n° » ou
   « Chapitre n° » attendu. Plutôt que de deviner ce qu'elles
   signifient, on les exclut de la structure pédagogique et on le dit
   dans `warnings` — jamais de contenu pédagogique inventé pour
   combler une ligne qu'on ne comprend pas.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import BinaryIO

import docx
from docx.table import Table

from app.ingestion.track_schema import HeaderColumns, detect_columns
from app.schemas.ingestion import (
    ParsedDocument,
    ParsedLearningUnit,
    ParsedModule,
    ParsedTeachingUnit,
)

MODULE_PATTERN = re.compile(r"^MODULE\s*N?°?\s*(\d+)\s*[:.]?\s*(.*)$", re.IGNORECASE | re.DOTALL)
# Le préfixe n'est volontairement pas figé à "UA"/"Chapitre" : le
# corpus réel contient aussi "UAE" pour désigner un chapitre (voir
# fiche_progression_niveau1.docx, ligne 18) — une troisième variante
# non documentée à l'avance. On accepte tout préfixe alphabétique
# court (1 à 20 lettres) suivi d'un numéro, plutôt que d'allonger sans
# fin une liste de préfixes connus. Un préfixe non vide exigé (au
# moins une lettre) écarte les lignes qui commencent directement par
# un numéro, comme les dates d'interruption de trimestre.
LEARNING_UNIT_PATTERN = re.compile(
    r"^[A-ZÀ-Ÿ]{1,20}\s*N?°?\s*(\d+)\s*[:.]?\s*(.*)$", re.IGNORECASE | re.DOTALL
)
# Ici le préfixe PEUT être vide : une unité d'enseignement réelle peut
# n'avoir aucun préfixe, juste "1 Connexion des périphériques..."
# (voir fiche_progression_seconde.docx). Le risque qu'une ligne de
# planning (non pédagogique) passe ce filtre est écarté en amont par
# `_is_content_row`, qui se prononce sur la cellule Module/UA de la
# même ligne avant qu'on n'atteigne cette cellule.
TEACHING_UNIT_PATTERN = re.compile(
    r"^[A-ZÀ-Ÿ]{0,20}\s*N?°?\s*(\d+)\s*[:.]?\s*(.*)$", re.IGNORECASE | re.DOTALL
)


def _clean(text: str) -> str:
    """Normalise une cellule brute : espaces insécables, retours à la
    ligne internes et espaces multiples deviennent un espace simple."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" :.\u2019'")


def _parse_digitalisation(raw: str, warnings: list[str], context: str) -> bool | None:
    normalized = _clean(raw).upper()
    if normalized == "OUI":
        return True
    if normalized == "NON":
        return False
    if normalized == "":
        return None
    # Une coquille comme "NION" (observée dans le corpus réel) n'est
    # jamais corrigée à la volée : on ne sait pas si c'était "NON" ou
    # autre chose. On le signale, l'enseignant tranche.
    warnings.append(
        f"Digitalisation illisible ({context}) : valeur brute « {raw.strip()} » ignorée."
    )
    return None


def _split_teaching_unit_cell(raw: str) -> list[str]:
    """Une cellule peut contenir plusieurs unités séparées par un saut
    de ligne. Un fragment qui ne commence pas par un numéro est traité
    comme la suite du titre précédent (repli sur les titres qui
    s'étendent sur plusieurs lignes sans numérotation répétée)."""
    fragments = [f for f in (raw or "").split("\n") if f.strip()]
    merged: list[str] = []
    for fragment in fragments:
        if TEACHING_UNIT_PATTERN.match(_clean(fragment)) or not merged:
            merged.append(fragment)
        else:
            merged[-1] += " " + fragment
    return merged


def _is_content_row(learning_unit_cell: str) -> bool:
    """Une ligne « ÉVALUATION », « REMEDIATION » ou toute autre note de
    planning ne présente jamais le motif attendu « UA n° »/« Chapitre
    n° ». On n'essaie pas de deviner son sens : on l'exclut."""
    return LEARNING_UNIT_PATTERN.match(_clean(learning_unit_cell)) is not None


def _warn_skipped_row(
    row_index: int,
    module_raw: str,
    learning_unit_raw: str,
    cells: list[str],
    columns: HeaderColumns,
    warnings: list[str],
) -> None:
    """Toujours signaler une ligne ignorée — jamais de disparition
    silencieuse. Certaines lignes n'ont ni Module ni UA/Chapitre
    renseignés mais portent quand même un contenu ailleurs (Actions,
    Digitalisation) — observé sur une ligne « Semaine 1 » de type
    orientation/prise de contact dans le corpus réel. On le dit."""
    note = _clean(learning_unit_raw) or _clean(module_raw)
    if note:
        warnings.append(f"Ligne {row_index} ignorée (pas une unité pédagogique) : « {note} ».")
        return

    autres_indices = {
        "Digitalisation": columns.digitalisation,
        "Actions": columns.actions,
    }
    fragments = []
    for label, index in autres_indices.items():
        if index is not None:
            value = _clean(cells[index])
            if value:
                fragments.append(f"{label} = « {value} »")

    if fragments:
        warnings.append(
            f"Ligne {row_index} ignorée (cellules Module et UA/Chapitre vides), "
            f"mais du contenu existe ailleurs sur cette ligne : {', '.join(fragments)}. "
            "Non rattaché à une unité pédagogique — à vérifier dans le document source."
        )
    else:
        warnings.append(f"Ligne {row_index} ignorée : entièrement vide.")


def _extract_optional_columns(row_cells: list[str], columns: HeaderColumns) -> dict:
    extra: dict[str, str | None] = {}
    if columns.actions is not None:
        extra["actions"] = _clean(row_cells[columns.actions]) or None
    if columns.essential_knowledge is not None:
        extra["essential_knowledge"] = _clean(row_cells[columns.essential_knowledge]) or None
    if columns.duration is not None:
        extra["duration_label"] = _clean(row_cells[columns.duration]) or None
    if columns.session_type is not None:
        extra["session_type"] = _clean(row_cells[columns.session_type]) or None
    return extra


def _parse_table(table: Table, kind: str) -> ParsedDocument:
    header = [cell.text for cell in table.rows[0].cells]
    columns, track_schema = detect_columns(header)

    warnings: list[str] = []
    # Modules et unités intermédiaires, dédupliqués par numéro car
    # répétés sur chaque ligne de la semaine correspondante (voir note
    # de conception en tête de fichier).
    modules: dict[str, ParsedModule] = {}
    learning_units: dict[tuple[str, str], ParsedLearningUnit] = {}

    for row_index, row in enumerate(table.rows[1:], start=2):
        cells = [c.text for c in row.cells]

        module_raw = cells[columns.module]
        learning_unit_raw = cells[columns.learning_unit]

        if not _is_content_row(learning_unit_raw):
            _warn_skipped_row(row_index, module_raw, learning_unit_raw, cells, columns, warnings)
            continue

        module_match = MODULE_PATTERN.match(_clean(module_raw))
        if not module_match:
            warnings.append(
                f"Ligne {row_index} : intitulé de module illisible « {module_raw.strip()} », ligne ignorée."
            )
            continue
        module_number, module_title = module_match.group(1), _clean(module_match.group(2))

        module = modules.setdefault(
            module_number, ParsedModule(number=module_number, title=module_title)
        )

        lu_match = LEARNING_UNIT_PATTERN.match(_clean(learning_unit_raw))
        if lu_match is None:
            # Ne devrait pas se produire : _is_content_row vient de
            # confirmer une correspondance avec le même motif — un
            # `if` explicite plutôt qu'un `assert` (retiré à la
            # compilation optimisée, voir bandit B101), pour rester
            # sûr même en Python lancé avec l'option -O.
            continue
        lu_number, lu_title = lu_match.group(1), _clean(lu_match.group(2))

        lu_key = (module_number, lu_number)
        learning_unit = learning_units.get(lu_key)
        if learning_unit is None:
            learning_unit = ParsedLearningUnit(number=lu_number, title=lu_title)
            learning_units[lu_key] = learning_unit
            module.learning_units.append(learning_unit)

        for fragment in _split_teaching_unit_cell(cells[columns.teaching_unit]):
            tu_match = TEACHING_UNIT_PATTERN.match(_clean(fragment))
            if not tu_match:
                warnings.append(
                    f"Ligne {row_index} : unité d'enseignement illisible « {fragment.strip()} », ignorée."
                )
                continue
            tu_number, tu_title = tu_match.group(1), _clean(tu_match.group(2))
            context = f"module {module_number}, unité {tu_number}"
            digitalized = _parse_digitalisation(cells[columns.digitalisation], warnings, context)

            teaching_unit = ParsedTeachingUnit(
                number=tu_number,
                title=tu_title,
                digitalized=digitalized,
                **_extract_optional_columns(cells, columns),
            )
            # Une unité déjà vue (répétée sur une semaine de rattrapage,
            # observé dans le corpus réel) n'est pas dupliquée.
            if not any(u.number == tu_number for u in learning_unit.teaching_units):
                learning_unit.teaching_units.append(teaching_unit)

    return ParsedDocument(
        kind=kind,  # type: ignore[arg-type]
        track_schema=track_schema,
        modules=list(modules.values()),
        warnings=warnings,
    )


def parse_docx(source: str | Path | BinaryIO, *, kind: str) -> ParsedDocument:
    """Point d'entrée public. `kind` est fourni par l'appelant (déduit
    du nom de fichier ou choisi explicitement à l'import — voir
    app/api/routes/ingestion.py), pas deviné depuis le contenu : deux
    documents peuvent avoir une structure de colonnes identique."""
    document = docx.Document(str(source) if isinstance(source, Path) else source)
    if not document.tables:
        return ParsedDocument(
            kind=kind,  # type: ignore[arg-type]
            track_schema="ua_ue",
            modules=[],
            warnings=["Aucun tableau trouvé dans le document."],
        )
    return _parse_table(document.tables[0], kind)
