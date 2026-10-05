# Contribuer à NkulIA

Merci de vous intéresser à NkulIA. Ce document explique comment le
travail est organisé, pour que chaque contribution — même solo —
reste traçable et cohérente avec les décisions actées dans `docs/adr/`.

## Avant de commencer

1. Lisez `README.md`, puis `docs/ARCHITECTURE.md` et les décisions
   d'architecture dans `docs/adr/` — en particulier le principe
   **offline-first** et le **modèle de provenance** (aucune donnée
   pédagogique officielle ne doit être inventée par le LLM).
2. Choisissez un ticket dans `docs/ISSUES.md`, en respectant les
   dépendances indiquées. Créez l'issue correspondante sur GitHub à
   partir des modèles `.github/ISSUE_TEMPLATE/` si elle n'existe pas
   encore.

## Convention de branches

```
<type>/<résumé-court-en-kebab-case>
```

Types : `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
Exemple : `feat/local-auth-teacher-profile`.

## Convention de commits et de PR

[Conventional Commits](https://www.conventionalcommits.org/fr/) — voir aussi `CONVENTIONAL_COMMITS.md` :

```
feat(auth): ajoute la connexion locale par email et mot de passe
fix(import): corrige la détection de la colonne Digitalisation
docs(adr): documente le choix de SQLite plutôt que Postgres
```

Chaque pull request doit :
- rester dans le scope d'une seule ligne de `docs/PULL_REQUESTS.md` ;
- référencer ses issues avec `Closes #<numéro>` ;
- remplir la checklist de `.github/PULL_REQUEST_TEMPLATE.md` ;
- passer la CI (lint + tests) avant toute demande de relecture.

## Avant chaque pull request

```bash
make lint     # ruff + mypy + bandit
make test     # pytest avec couverture
```

(`make install` installe aussi les hooks `pre-commit` ; `make precommit` les exécute à la demande.)

## Règles non négociables (rappel — détail dans `docs/adr/`)

- **Offline-first** : aucune fonctionnalité MVP n'exige une connexion
  réseau permanente. Pas de dépendance à un serveur toujours actif.
- **Provenance obligatoire** : tout contenu généré porte l'une des
  quatre étiquettes (`reference`, `deduction`, `ai_recommendation`,
  `missing_information`).
- **Validation humaine avant export** : le statut `validé` est requis
  avant tout rendu PDF définitif.
- **`track_schema` neutre** : jamais de nom de filière (`UA/UE`,
  `Chapitre/Leçon`) codé en dur dans le schéma relationnel.

## Publier une nouvelle version

Les versions suivent [Semantic Versioning](https://semver.org/lang/fr/).
Un tag `vX.Y.Z` déclenche la construction de l'exécutable Windows et sa
publication en Release GitHub (voir `.github/workflows/release.yml` — c'est l'équivalent « CD » de
ce projet, adapté à une application de bureau plutôt qu'à un service
web). Les notes de version sont générées depuis les commits : d'où
l'importance des Conventional Commits. La Release est créée en
**brouillon** : lancez l'exécutable une fois avant de la publier.
