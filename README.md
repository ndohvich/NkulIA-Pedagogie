<div align="center">

# NkulIA

**Environnement intelligent de conception, de planification, de génération et de suivi pédagogique pour les enseignants du secondaire camerounais.**

*La voix pédagogique qui porte, du programme jusqu'à la salle de classe.*

![Statut](https://img.shields.io/badge/statut-en%20d%C3%A9veloppement-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Licence](https://img.shields.io/badge/licence-%C3%A0%20d%C3%A9finir-lightgrey)
[![Conventional Commits](https://img.shields.io/badge/commits-conventional-%23FE5196)](https://www.conventionalcommits.org/fr/v1.0.0/)

[English version](./README.en.md)

</div>

---

## Le problème

Un enseignant camerounais dispose déjà, dans son établissement, de
documents de référence (fiches de progression, projets pédagogiques)
qui décrivent précisément le programme officiel. Aujourd'hui, il
reformule manuellement ces documents en cours, fiches, exercices et
évaluations — une tâche répétitive, chronophage, et sans garantie de
cohérence entre ce qui a été enseigné et ce qui est évalué.

## Ce que fait NkulIA

NkulIA importe vos documents pédagogiques existants, en comprend la
structure (module → unité d'apprentissage/chapitre → unité
d'enseignement/leçon), et génère des cours, fiches, situations-problèmes,
exercices et évaluations — chaque information étant explicitement
étiquetée selon sa provenance :

| Étiquette | Signification |
|---|---|
| 🟢 Référence | Reprise telle quelle du document importé |
| 🔵 Déduction | Inférée à partir de plusieurs éléments du référentiel |
| 🟡 Recommandation IA | Générée par le modèle, sans correspondance directe |
| ⚪ Information manquante | Absente du référentiel — jamais inventée |

**L'enseignant reste le décideur.** Rien n'est exporté en PDF définitif
sans validation humaine explicite.

## Ce que NkulIA n'est pas

- Pas un chatbot générique : sans référentiel structuré en entrée, il
  ne génère rien et le dit clairement.
- Pas un service en ligne : l'application fonctionne **hors-ligne par
  défaut** (voir [`docs/adr/0001`](docs/adr/0001-architecture-offline-first.md)).

## Architecture

```
┌─────────────────────────────────────────────┐
│  Fenêtre PyWebView (shell natif Windows)     │
│  ┌─────────────────────────────────────────┐ │
│  │  Frontend React + Vite + Tailwind        │ │
│  └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │  Backend FastAPI (même processus)        │ │
│  │  ├── Auth locale (Argon2)                │ │
│  │  ├── Import & structuration (RAG)        │ │
│  │  ├── Génération (LLM + provenance)       │ │
│  │  └── Export PDF                          │ │
│  └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │  SQLite local (SQLAlchemy + Alembic)     │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

Décisions détaillées et alternatives écartées : [`docs/adr/`](docs/adr/).
Vue complète : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Stack technique

| Couche | Choix |
|---|---|
| Interface (fenêtre native) | PyWebView |
| Frontend | React + Vite + Tailwind CSS |
| Backend / API | FastAPI (Python) |
| Base de données | SQLite (SQLAlchemy + Alembic) |
| Recherche pédagogique | RAG embarqué, sans serveur externe |
| Packaging Windows | PyInstaller |

## Démarrage — développement local

```bash
git clone https://github.com/ndohvich/NkulIA-Pedagogie.git
cd NkulIA-Pedagogie

# Backend
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -e "./backend[dev]"

# Frontend
cd frontend && npm install && cd ..

# Lancer l'application (fenêtre PyWebView + API locale)
python desktop/main.py
```

Détail complet des commandes de qualité (lint, tests) : voir
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Configuration de la génération

Par défaut, NkulIA fonctionne **sans réseau** (fournisseur `offline` : il
recopie le référentiel et marque le reste « information manquante »).
Pour activer un modèle de langage distant (optionnel) :

| Variable | Rôle |
|---|---|
| `NKULIA_LLM_PROVIDER` | `offline` (défaut) ou `anthropic` |
| `NKULIA_LLM_API_KEY` | clé API — uniquement par variable d'environnement, jamais dans le code ni la base |
| `NKULIA_LLM_MODEL` | modèle utilisé (défaut dans `backend/app/core/config.py`) |

Voir [`docs/adr/0005`](docs/adr/0005-fournisseur-de-generation.md).

## Feuille de route

| Phase | Contenu | Statut |
|---|---|---|
| 1 — Discovery | Analyse du besoin et du corpus pédagogique réel | ✅ |
| 2 — Architecture | Stack, schéma de données, ADR | ✅ |
| 3 — Fondations | Gouvernance, outillage qualité, authentification locale | ✅ |
| 4 — MVP | Import, sélection pédagogique, génération de cours, export PDF | ✅ (premier gabarit : fiche de cours) |
| 5 — Intelligence avancée | RAG complet, assistant conversationnel, examens | ⏳ |
| 6 — Industrialisation | Packaging release, sauvegardes, durcissement sécurité | ⏳ |

Backlog détaillé : [`docs/ISSUES.md`](docs/ISSUES.md) · Plan de PR : [`docs/PULL_REQUESTS.md`](docs/PULL_REQUESTS.md)

## Contribuer

Voir [`CONTRIBUTING.md`](CONTRIBUTING.md) pour les conventions de
branches, de commits ([`CONVENTIONAL_COMMITS.md`](CONVENTIONAL_COMMITS.md))
et le processus de revue.

## Licence

**À définir.** Ce projet n'a pas encore de licence officielle — ne pas
réutiliser en attendant qu'elle soit publiée dans `LICENSE`.

## Auteur

Développé par [Jules Yannick](https://github.com/ndohvich), enseignant-chercheur
au Laboratoire Signaux, Images et Systèmes (LaSIS/SIS), ENSET Ébolowa,
Cameroun.
