# ADR-0005 : Fournisseur de génération interchangeable, hors-ligne par défaut

- **Statut** : accepté
- **Date** : 2026-10-02

## Contexte

La génération doit fonctionner sur un poste à connexion instable
(ADR-0001), mais la qualité d'une situation-problème ou d'un
déroulement d'activités dépend d'un modèle de langage, aujourd'hui
disponible par API distante. Il faut aussi une « recherche
pédagogique » (le R de RAG) sans serveur à installer.

## Décision

- Une interface `LLMProvider` (`app/generation/providers.py`) avec deux
  implémentations : `OfflineProvider` (déterministe, sans modèle, **par
  défaut**) et `AnthropicProvider` (API distante, activée par
  `NKULIA_LLM_PROVIDER=anthropic` et `NKULIA_LLM_API_KEY`).
- La clé API vient uniquement de l'environnement ; elle n'est jamais
  écrite en base ni dans les logs, et jamais recopiée dans un message
  d'erreur.
- Le fournisseur ne reçoit que le contexte d'**une** unité (champs du
  référentiel + quelques unités voisines) et ne produit que les champs
  génératifs ; la structure pédagogique est imposée par l'application.
- Recherche embarquée : classement lexical (indice de Jaccard sur mots
  normalisés), sans base vectorielle ni embeddings à télécharger.

## Alternatives considérées

| Option | Avantages | Inconvénients | Retenue ? |
|---|---|---|---|
| LLM distant obligatoire | Meilleure qualité immédiate | Inutilisable sans réseau, contraire à ADR-0001 | Non |
| Modèle local embarqué | Hors-ligne et génératif | Plusieurs Go, matériel exigeant sur des postes modestes | Non (à réévaluer en phase 5) |
| Base vectorielle (LanceDB) dès le MVP | Recherche sémantique | Dépendance lourde, modèle d'embeddings à télécharger | Non pour le MVP |
| **Interface + hors-ligne par défaut + distant optionnel** | Fonctionne partout, qualité si réseau | Deux chemins à tester | **Oui** |

## Conséquences

- Le comportement hors-ligne est honnête mais pauvre : il produit les
  champs de référence, une déduction de prérequis et marque le reste
  « information manquante ».
- Le critère « fiche jugée exploitable » (issue #13) se vérifie avec le
  fournisseur distant et une revue humaine ; les tests automatisés
  utilisent un transport simulé.
- Changer de fournisseur ou de modèle = une variable d'environnement.

## Réversibilité

Facile : le pipeline ne dépend que de l'interface.
