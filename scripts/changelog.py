#!/usr/bin/env python3
"""Génère les notes de version depuis les commits Conventional Commits
(issue #15 — voir CONVENTIONAL_COMMITS.md).

    python scripts/changelog.py --tag v0.1.0            # notes entre le tag précédent et v0.1.0
    python scripts/changelog.py --tag v0.1.0 --previous v0.0.0

Sans dépendance externe : uniquement la bibliothèque standard et `git`.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — appel de `git` avec arguments fixes, sans shell
import sys
from collections import defaultdict

# type -> titre de section, dans l'ordre d'affichage. Les types absents d'ici
# (chore, style, test, ci, build) ne figurent pas dans les notes : ce sont des
# détails d'outillage, pas des changements visibles par un enseignant.
SECTIONS = {
    "feat": "Nouveautés",
    "fix": "Corrections",
    "perf": "Performances",
    "docs": "Documentation",
    "refactor": "Améliorations internes",
}

_HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$")


def parse_subject(subject: str) -> tuple[str, str | None, bool, str] | None:
    """`feat(auth)!: texte` -> ("feat", "auth", True, "texte") ; None si non conforme."""
    match = _HEADER.match(subject.strip())
    if not match:
        return None
    return match["type"], match["scope"], bool(match["breaking"]), match["desc"].strip()


def build_notes(commits: list[tuple[str, str]], tag: str) -> str:
    """`commits` : liste de (sujet, corps). Renvoie les notes en Markdown."""
    grouped: dict[str, list[str]] = defaultdict(list)
    breaking: list[str] = []
    skipped = 0

    for subject, body in commits:
        parsed = parse_subject(subject)
        if parsed is None:
            skipped += 1
            continue
        kind, scope, is_breaking, description = parsed
        line = f"- {f'**{scope}** : ' if scope else ''}{description}"
        if is_breaking or "BREAKING CHANGE" in body:
            breaking.append(line)
        if kind in SECTIONS:
            grouped[kind].append(line)

    parts = [f"## NkulIA {tag}", ""]
    if breaking:
        parts += ["### ⚠ Changements incompatibles", *breaking, ""]
    for kind, title in SECTIONS.items():
        if grouped[kind]:
            parts += [f"### {title}", *grouped[kind], ""]
    if len(parts) == 2:
        parts += ["Aucun changement visible dans cette version.", ""]
    if skipped:
        parts += [f"_{skipped} commit(s) non conformes à Conventional Commits ignoré(s)._", ""]
    return "\n".join(parts).rstrip() + "\n"


def _git(*args: str) -> str:
    return subprocess.run(  # nosec B603 B607 — `git` fixe, arguments contrôlés, pas de shell
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout


def previous_tag(tag: str) -> str | None:
    """Tag `v*.*.*` le plus récent AVANT `tag`, ou None pour la toute première version."""
    tags = [t for t in _git("tag", "--list", "v*.*.*", "--sort=-v:refname").split() if t != tag]

    def key(name: str) -> tuple[int, ...]:
        return tuple(int(n) for n in re.findall(r"\d+", name))

    older = [t for t in tags if key(t) < key(tag)]
    return max(older, key=key) if older else None


def commits_between(previous: str | None, tag: str) -> list[tuple[str, str]]:
    revision = f"{previous}..{tag}" if previous else tag
    raw = _git("log", revision, "--no-merges", "--format=%s%x1f%b%x1e")
    commits = []
    for record in raw.split("\x1e"):
        if record.strip():
            subject, _, body = record.strip().partition("\x1f")
            commits.append((subject, body))
    return commits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--previous", default=None, help="tag de départ (défaut : tag précédent)")
    args = parser.parse_args()

    previous = args.previous or previous_tag(args.tag)
    sys.stdout.write(build_notes(commits_between(previous, args.tag), args.tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
