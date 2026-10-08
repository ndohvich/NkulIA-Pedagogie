# Architecture

Ce document décrit *comment* le système est construit. Le *pourquoi*
de chaque choix structurant est dans [`docs/adr/`](adr/) — ce document
n'y revient pas en détail, il s'appuie dessus.

## Principes non négociables

1. **Offline-first** — voir [ADR-0001](adr/0001-architecture-offline-first.md). Aucune fonctionnalité du MVP ne doit exiger une connexion réseau permanente.
2. **Provenance obligatoire** — tout contenu généré porte l'une de ces quatre étiquettes : `reference`, `deduction`, `ai_recommendation`, `missing_information`. Un contenu étiqueté `reference` sans pointeur vers le document source est un bug, pas une fonctionnalité.
3. **Validation humaine avant export** — un document passe par les statuts `brouillon → analysé → proposé → modifié → validé` ; seul `validé` autorise l'export PDF définitif.
4. **`track_schema` neutre** — voir [ADR-0003](adr/0003-sqlite-plutot-que-postgres.md). Le vocabulaire d'une filière (UA/UE vs Chapitre/Leçon) est une donnée de configuration, jamais un nom de colonne ou de table.

## Vue C4 — Niveau 1 : Contexte système

```mermaid
C4Context
    Person(teacher, "Enseignant", "Utilise NkulIA sur son poste Windows")
    System(nkulia, "NkulIA", "Application de bureau locale : import, génération, export pédagogique")
    System_Ext(llm, "Fournisseur LLM", "API distante, appelée uniquement pour la génération (optionnelle hors-ligne)")

    Rel(teacher, nkulia, "Importe des documents, sélectionne des unités, valide et exporte des fiches")
    Rel(nkulia, llm, "Envoie le contexte pédagogique pertinent, reçoit une proposition structurée", "HTTPS, ponctuel")
```

## Vue C4 — Niveau 2 : Conteneurs

```mermaid
C4Container
    Person(teacher, "Enseignant")

    System_Boundary(app, "NkulIA (un seul processus, un seul poste)") {
        Container(shell, "Shell PyWebView", "Python", "Fenêtre native Windows, charge l'interface web")
        Container(frontend, "Frontend", "React + Vite + Tailwind", "Dashboard, import, sélection, génération, validation")
        Container(api, "API locale", "FastAPI", "Auth, import, RAG, génération, export PDF")
        ContainerDb(db, "Base locale", "SQLite", "Contexte enseignant, contenus générés, historique")
    }

    System_Ext(llm, "Fournisseur LLM")

    Rel(teacher, shell, "Utilise")
    Rel(shell, frontend, "Affiche")
    Rel(frontend, api, "Appelle", "HTTP local (127.0.0.1)")
    Rel(api, db, "Lit / écrit", "SQL")
    Rel(api, llm, "Génère du contenu", "HTTPS, si réseau disponible")
```

## Vue C4 — Niveau 3 : Composants de l'API

```mermaid
C4Component
    Container_Boundary(api, "API FastAPI") {
        Component(auth, "Auth", "Router", "Inscription, connexion, session locale (Argon2)")
        Component(profile, "Profil", "Router", "Contexte enseignant / établissement")
        Component(ingestion, "Ingestion", "Service", "Parsing DOCX/PDF, détection de structure")
        Component(rag, "RAG", "Service", "Indexation et recherche du référentiel pédagogique")
        Component(generation, "Génération", "Service", "Appel LLM + application du modèle de provenance")
        Component(pdf, "Export PDF", "Service", "Rendu des gabarits de documents finaux")
        ComponentDb(db, "SQLite", "SQLAlchemy + Alembic")
    }

    Rel(auth, db, "lit/écrit")
    Rel(profile, db, "lit/écrit")
    Rel(ingestion, db, "écrit le référentiel structuré")
    Rel(rag, db, "indexe / interroge")
    Rel(generation, rag, "récupère le contexte pertinent")
    Rel(generation, db, "écrit le contenu généré + provenance")
    Rel(pdf, db, "lit le contenu validé")
```

## Modèle de données (extrait — MVP)

```
Institution 1───* Teacher
Institution 1───* SchoolYear
Institution 1───* Classroom *───1 SchoolYear
Teacher 1───* AuthSession
Teacher *───* Classroom (via TeachingAssignment) *───* Subject
Classroom 1───* SourceDocument 1───* Module 1───* LearningUnit 1───* TeachingUnit
Teacher 1───* GeneratedDocument *───1 TeachingUnit ; GeneratedDocument 1───* GeneratedField
```

Détail des champs : voir les modèles SQLAlchemy dans `backend/app/db/models.py`
(ajoutés en [PR-03](PULL_REQUESTS.md#pr-03--featauth-persist-teacher-context-and-local-authentication)).

## Contrat de génération (extrait)

Toute réponse du service de génération respecte ce schéma minimal :

```json
{
  "field": "objectif_general",
  "value": "Identifier et connecter les périphériques d'un ordinateur",
  "provenance": "reference",
  "source_ref": "fiche_progression_seconde.docx#L42"
}
```

`provenance` ∈ `{reference, deduction, ai_recommendation, missing_information}`.
`source_ref` est obligatoire si `provenance = reference`, absent sinon.
Un contrôle automatisé (issue [#12](ISSUES.md#12--modèle-de-provenance-dans-le-pipeline-de-génération))
rejette toute réponse qui ne respecte pas ce contrat avant qu'elle
n'atteigne l'interface.

## Ce qui est explicitement hors périmètre (et pourquoi)

| Hors périmètre | Raison |
|---|---|
| Déploiement serveur (Render, Fly.io, VPS) | Pas de serveur : voir ADR-0001 |
| Postgres, Redis, Celery | Pas de charge concurrente ni de tâche de fond partagée : voir ADR-0003 |
| Prometheus / Grafana | Rien à superviser en continu, pas de service toujours actif |
| Synchronisation multi-postes | Hors MVP — ferait l'objet d'un nouvel ADR si un besoin réel apparaît |
