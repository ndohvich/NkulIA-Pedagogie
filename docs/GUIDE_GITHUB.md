# Guide GitHub — issues et pull requests de NkulIA

Ce guide correspond **exactement** à `docs/ISSUES.md` (15 issues) et
`docs/PULL_REQUESTS.md` (8 PR). Chaque commande est copiable telle quelle
avec la [CLI GitHub](https://cli.github.com/) (`gh auth login` une fois) ;
tout peut aussi se faire dans l'interface web.

## Règle qui évite les mauvais numéros

**Les issues et les pull requests partagent la même numérotation** sur
GitHub. Si vous ouvrez une PR entre deux issues, elle prend un numéro et
décale les suivantes — et vos `Closes #12` pointeraient vers le mauvais
ticket. Donc : **créez d'abord les 15 issues d'un coup** (étape 1), vérifiez
qu'elles portent bien les numéros #1 à #15, puis seulement ouvrez les PR.

Si votre dépôt contient déjà des issues/PR, les numéros seront décalés :
relevez les vrais numéros avec `gh issue list --state all` et adaptez les
`Closes #…` des messages de commit **avant** de pousser.

## Étape 0 — Préparer les labels

```bash
cd NkulIA-Pedagogie
scripts/sync_labels.sh      # crée/met à jour les labels de .github/labels.yml (type:, priority:, effort:, domain:, status:)
gh label list
```

## Étape 1 — Créer les 15 issues (dans l'ordre)

### Issue #1 — Mettre en place pre-commit et consolider `pyproject.toml`
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'Mettre en place pre-commit et consolider `pyproject.toml`' \
  --label "type: chore" --label "priority: P1" --label "effort: S" --label "domain: ci" \
  --body 'Configurer `black`, `ruff` (remplace isort + flake8), `mypy` et `bandit` en hooks `pre-commit`. Centraliser toutes les dépendances et la config des outils dans `backend/pyproject.toml`.

**Terminé lorsque** : `pre-commit run --all-files` passe sans erreur sur le code existant.

Dépend de : rien'
```

### Issue #2 — Créer le `Makefile` de développement
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'Créer le `Makefile` de développement' \
  --label "type: chore" --label "priority: P1" --label "effort: S" --label "domain: ci" \
  --body 'Cibles `make install`, `make lint`, `make test`, `make run`.

**Terminé lorsque** : ces 4 commandes fonctionnent sur un clone neuf.

Dépend de : #1'
```

### Issue #3 — CI GitHub Actions : lint + tests sur chaque PR
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'CI GitHub Actions : lint + tests sur chaque PR' \
  --label "type: chore" --label "priority: P0" --label "effort: M" --label "domain: ci" \
  --body 'Workflow déclenché sur `push` et `pull_request`, matrice Python 3.11/3.12, cache pip.

**Terminé lorsque** : une PR avec une erreur de lint ou un test cassé est bloquée automatiquement.

Dépend de : #1, #2'
```

### Issue #4 — Ajouter l'analyse de sécurité statique (CodeQL)
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'Ajouter l'"'"'analyse de sécurité statique (CodeQL)' \
  --label "type: chore" --label "priority: P2" --label "effort: S" --label "domain: ci" \
  --body 'Workflow CodeQL natif GitHub (pas de compte tiers).

**Terminé lorsque** : l'"'"'onglet Security > Code scanning affiche des résultats.

Dépend de : #3'
```

### Issue #5 — Modéliser le contexte enseignant + migrations Alembic
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'Modéliser le contexte enseignant + migrations Alembic' \
  --label "type: feat" --label "priority: P0" --label "effort: M" --label "domain: backend" \
  --body 'Modèles `Teacher`, `Institution`, `SchoolYear`, `Subject`, `Classroom`, `TeachingAssignment` (voir `docs/ARCHITECTURE.md`). Première révision Alembic.

**Terminé lorsque** : `alembic upgrade head` crée un schéma propre sur base vide, `alembic downgrade base` le défait proprement.

Dépend de : #1'
```

### Issue #6 — Inscription et connexion locale
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'Inscription et connexion locale' \
  --label "type: feat" --label "priority: P0" --label "effort: M" --label "domain: backend" \
  --body 'Hachage Argon2, jeton de session opaque stocké en base (pas de JWT — inutile en local). Endpoints `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`.

**Terminé lorsque** : un email déjà utilisé est refusé, un mauvais mot de passe est refusé, une session expirée est refusée.

Dépend de : #5'
```

### Issue #7 — Endpoint de gestion du profil
*Statut : ✅ déjà dans votre dépôt (vague 3)*

```bash
gh issue create \
  --title 'Endpoint de gestion du profil' \
  --label "type: feat" --label "priority: P1" --label "effort: S" --label "domain: backend" \
  --body '`GET /me`, `PATCH /me` (grade, fonction, spécialité, établissement).

**Terminé lorsque** : les champs pré-remplissent un export PDF de test.

Dépend de : #6'
```

### Issue #8 — Écrans React Connexion / Inscription / Profil
*Statut : 🆕 PR préliminaire + PR-04*

```bash
gh issue create \
  --title 'Écrans React Connexion / Inscription / Profil' \
  --label "type: feat" --label "priority: P1" --label "effort: M" --label "domain: frontend" \
  --body 'Reprendre fidèlement le prototype HTML déjà validé (palette, fil pédagogique, badges de provenance).

**Terminé lorsque** : le parcours inscription → connexion → profil fonctionne de bout en bout dans l'"'"'app desktop.

Dépend de : #6, #7'
```

### Issue #9 — Parseur DOCX (fiches de progression / projets pédagogiques)
*Statut : ✅ vague 3*

```bash
gh issue create \
  --title 'Parseur DOCX (fiches de progression / projets pédagogiques)' \
  --label "type: feat" --label "priority: P0" --label "effort: L" --label "domain: backend" \
  --body 'Extraction des tableaux, détection des colonnes (Module, UA/Chapitre, UE/Leçon, Digitalisation, et colonnes optionnelles du projet pédagogique).

**Terminé lorsque** : les 7 documents du corpus réel (Seconde à Terminale, Niveau 1/2) sont importés sans erreur.

Dépend de : #5'
```

### Issue #10 — Détection automatique du schéma de filière
*Statut : ✅ vague 3*

```bash
gh issue create \
  --title 'Détection automatique du schéma de filière' \
  --label "type: feat" --label "priority: P0" --label "effort: M" --label "domain: backend" \
  --body 'Reconnaître automatiquement si un document utilise le vocabulaire « UA/UE » ou « Chapitre/Leçon » et le normaliser vers le modèle neutre (voir `docs/adr/0003`).

**Terminé lorsque** : les deux vocabulaires produisent la même structure en base.

Dépend de : #9'
```

### Issue #11 — Écran Import & analyse
*Statut : 🆕 PR-06*

```bash
gh issue create \
  --title 'Écran Import & analyse' \
  --label "type: feat" --label "priority: P1" --label "effort: M" --label "domain: frontend" \
  --body 'Zone de dépôt, liste des documents importés, statut d'"'"'extraction, aperçu de la hiérarchie détectée.

**Terminé lorsque** : un enseignant peut importer un fichier et voir le résultat sans lire les logs backend.

Dépend de : #9, #10'
```

### Issue #12 — Modèle de provenance dans le pipeline de génération
*Statut : 🆕 PR-07*

```bash
gh issue create \
  --title 'Modèle de provenance dans le pipeline de génération' \
  --label "type: feat" --label "priority: P0" --label "effort: L" --label "domain: backend" \
  --body 'Chaque champ généré porte l'"'"'une des 4 étiquettes (référence, déduction, recommandation IA, information manquante) — voir `docs/adr/` et le principe non négociable du modèle de cadrage.

**Terminé lorsque** : un test automatisé vérifie qu'"'"'aucune sortie de génération n'"'"'est dépourvue d'"'"'étiquette de provenance.

Dépend de : #10'
```

### Issue #13 — Générateur de fiche de cours (premier gabarit)
*Statut : 🆕 PR-07*

```bash
gh issue create \
  --title 'Générateur de fiche de cours (premier gabarit)' \
  --label "type: feat" --label "priority: P1" --label "effort: L" --label "domain: backend" \
  --body 'Génération d'"'"'une fiche complète (objectifs, prérequis, situation-problème, activités) à partir d'"'"'une unité sélectionnée.

**Terminé lorsque** : une fiche générée sur une unité du corpus réel est jugée exploitable par l'"'"'enseignant (revue manuelle).

Dépend de : #12'
```

### Issue #14 — Export PDF d'une fiche validée
*Statut : 🆕 PR-08*

```bash
gh issue create \
  --title 'Export PDF d'"'"'une fiche validée' \
  --label "type: feat" --label "priority: P1" --label "effort: M" --label "domain: backend" \
  --body 'Gabarit PDF professionnel (en-tête établissement, identité visuelle NkulIA).

**Terminé lorsque** : le PDF généré est visuellement conforme au gabarit défini dans le dossier de cadrage.

Dépend de : #13'
```

### Issue #15 — Workflow de release desktop
*Statut : 🆕 PR-08*

```bash
gh issue create \
  --title 'Workflow de release desktop' \
  --label "type: chore" --label "priority: P2" --label "effort: M" --label "domain: desktop" \
  --body 'Sur tag `v*.*.*` : build PyInstaller, publication de l'"'"'exécutable en Release GitHub, changelog généré depuis les commits Conventional Commits (voir `CONVENTIONAL_COMMITS.md`).

**Terminé lorsque** : un tag de test produit une Release GitHub avec un `.exe` téléchargeable.

Dépend de : #2'
```

Vérification : `gh issue list --state all --limit 20` doit afficher #1 à #15
dans l'ordre. Pour les issues marquées ✅, fermez-les avec un commentaire
renvoyant vers la PR qui les a livrées (ou laissez-les ouvertes si leur PR n'a
pas encore été fusionnée dans votre dépôt).

## Étape 2 — Les 8 pull requests

Principe pour chacune : branche depuis `main` à jour → commit Conventional
Commits → push → `gh pr create` avec `Closes #…` → CI verte → relecture
(`.github/CODEOWNERS`) → *Squash and merge* → `git checkout main && git pull`.
**N'ouvrez la PR suivante qu'après la fusion de la précédente** : chaque PR
dépend des précédentes (`docs/PULL_REQUESTS.md`).

| PR | Titre | Closes | Statut |
|---|---|---|---|
| PR-01 | `chore: bootstrap quality tooling` | #1, #2 | ✅ dans l'état importé |
| PR-02 | `ci: add quality gate and CodeQL` | #3, #4 | ✅ dans l'état importé |
| PR-03 | `feat(auth): persist teacher context and local authentication` | #5, #6 | ✅ dans l'état importé |
| PR-04 | `feat(auth): profile endpoint and screens` | #7, #8 | #7 ✅ ; **#8 livré dans ce lot** |
| PR-05 | `feat(import): parse pedagogical DOCX documents` | #9, #10 | ✅ dans l'état importé |
| PR-06 | `feat(import): import & analysis screen` | #11 | 🆕 ce lot |
| PR-07 | `feat(generation): enforce provenance model in generation pipeline` | #12, #13 | 🆕 ce lot |
| PR-08 | `feat(release): PDF export and desktop release workflow` | #14, #15 | 🆕 ce lot |

### Récupérer les branches préparées

Le dossier fourni est un dépôt Git dont l'historique contient, dans l'ordre,
les commits prêts à publier. Branches locales (empilées) :

| Ordre | Branche | Contenu | Titre de PR |
|---|---|---|---|
| 0 | `fix/backend-packaging` | correctif d'installation (`pyproject.toml`) | `fix(build): declare python-docx and limit package discovery` |
| 1 | `feat/profile-screens` | écrans Connexion/Inscription/Profil + `institution_name` | `feat(auth): profile screens and editable institution` |
| 2 | `feat/import-screen` | écran Import & analyse, routes classes/matières | `feat(import): import & analysis screen` |
| 3 | `feat/generation-provenance` | provenance, pipeline, fiche de cours | `feat(generation): enforce provenance model in generation pipeline` |
| 4 | `feat/pdf-export-release` | export PDF + workflow de release | `feat(release): PDF export and desktop release workflow` |

Le premier commit (`chore: état importé`) est **votre** état de départ : si
`main` de votre dépôt est déjà identique, ne le publiez pas. Le plus sûr :
dans votre clone, ajoutez ce dossier comme remote local et récupérez les
branches :

```bash
git remote add lot ../chemin/vers/NkulIA-Pedagogie-lot   # le dossier fourni
git fetch lot
```

### PR préliminaire — correctif d'installation (aucune issue)

```bash
git checkout main && git pull
git checkout -b fix/backend-packaging lot/fix/backend-packaging
git push -u origin fix/backend-packaging
gh pr create --base main --head fix/backend-packaging \
  --title 'fix(build): declare python-docx and limit package discovery' \
  --body "## Résumé
\`pip install -e \"./backend[dev]\"\` échouait sur un clone neuf (setuptools découvrait \`app\` et \`migrations\`) et python-docx, importé par le parseur, n'était que dans l'extra \`rag\`.

## Comment tester
Clone neuf, \`make install && make test\`."
```

### PR-04 (partie #8) — `feat(auth): profile screens and editable institution`

```bash
git checkout main && git pull
git checkout -b feat/profile-screens lot/feat/profile-screens
git push -u origin feat/profile-screens
gh pr create --base main --head feat/profile-screens \
  --title 'feat(auth): profile screens and editable institution' \
  --body "Closes #8

## Résumé
Écrans React Connexion / Inscription / Profil branchés à l'API. Ajoute \`institution_name\` à \`PATCH /me\` (prévu par #7 mais absent du code) : il alimente l'en-tête des exports PDF.

## Périmètre
Hors scope : changement de mot de passe (ticket futur).

## Comment tester
\`make test\` ; parcours manuel : inscription → connexion → profil → déconnexion. **Joindre une capture d'écran** (exigé par docs/PULL_REQUESTS.md)."
```

### PR-06 — `feat(import): import & analysis screen`

```bash
git checkout main && git pull
git checkout -b feat/import-screen lot/feat/import-screen
git push -u origin feat/import-screen
gh pr create --base main --head feat/import-screen \
  --title 'feat(import): import & analysis screen' \
  --body "Closes #11

## Résumé
Zone de dépôt, statut des imports (succès ET échecs visibles), liste des documents, aperçu de la hiérarchie détectée. Ajoute les routes classes/matières (indispensables : l'import exige une classe et une matière, rien ne permettait de les créer) et \`GET /ingestion/documents/{id}\`.

## Comment tester
\`make test\` ; importer \`backend/tests/fixtures/fiche_progression_seconde.docx\` puis un fichier .pdf renommé : les deux résultats doivent être clairs à l'écran. **Joindre deux captures** (import réussi, import en échec)."
```

### PR-07 — `feat(generation): enforce provenance model in generation pipeline`

```bash
git checkout main && git pull
git checkout -b feat/generation-provenance lot/feat/generation-provenance
git push -u origin feat/generation-provenance
gh pr create --base main --head feat/generation-provenance \
  --title 'feat(generation): enforce provenance model in generation pipeline' \
  --body "Closes #12, #13

## Résumé
Contrat de provenance (4 étiquettes obligatoires, références vérifiées contre le document source), pipeline de génération, recherche pédagogique embarquée, fournisseur hors-ligne par défaut + fournisseur Anthropic optionnel, cycle brouillon → validé. ADR-0004 et ADR-0005.

## Périmètre
Hors scope : évaluations/examens (backlog futur).

## Comment tester
\`make test\`. **Revue manuelle exigée par #13** : avec une clé API (\`NKULIA_LLM_PROVIDER=anthropic\`), générer une fiche sur une unité du corpus réel et juger si elle est exploitable ; consigner le verdict dans la PR."
```

### PR-08 — `feat(release): PDF export and desktop release workflow`

```bash
git checkout main && git pull
git checkout -b feat/pdf-export-release lot/feat/pdf-export-release
git push -u origin feat/pdf-export-release
gh pr create --base main --head feat/pdf-export-release \
  --title 'feat(release): PDF export and desktop release workflow' \
  --body "Closes #14, #15

## Résumé
Export PDF d'une fiche validée (gabarit NkulIA, en-tête issu du profil). Release desktop : notes générées depuis les commits, migrations automatiques au démarrage de l'exécutable, base dans le dossier de données utilisateur.

## Comment tester
\`make test\` ; valider une fiche puis l'exporter. Pour #15 : \`git tag v0.1.0-test && git push origin v0.1.0-test\` → une Release **brouillon** avec un .zip doit apparaître ; télécharger, lancer NkulIA.exe, créer un compte. Supprimer ensuite le tag et la Release de test."
```

## Étape 3 — Après la dernière fusion

1. Vérifiez que #1 à #15 sont fermées (`gh issue list --state open`).
2. Renommez la section `[Non publié]` de `CHANGELOG.md` en `[0.1.0]`, puis `git tag v0.1.0 && git push origin v0.1.0`.
3. Ouvrez le brouillon de Release, lancez l'exécutable une fois, publiez.
