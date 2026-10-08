# ADR-0004 : Modèle de provenance et contenu modifié par l'enseignant

- **Statut** : accepté
- **Date** : 2026-10-02

## Contexte

Un LLM peut produire un texte pédagogique plausible mais inventé :
module qui n'existe pas, durée fantaisiste, « référence » à un document
qui ne dit pas cela. Pour un enseignant qui engage sa responsabilité
devant une classe, une information inventée présentée comme fiable est
pire qu'une case vide. Il faut aussi décider ce que devient une
information que l'enseignant complète ou corrige lui-même.

## Décision

1. **Quatre étiquettes, obligatoires et exclusives** sur tout champ
   généré : `reference`, `deduction`, `ai_recommendation`,
   `missing_information` (contrat : `app/generation/provenance.py`).
2. **`reference` est vérifiable, pas déclaratif.** Le pipeline recopie
   lui-même les champs de référence depuis la base ; un champ étiqueté
   `reference` doit citer un `source_ref` existant ET reprendre son texte
   fidèlement, sinon la sortie est rejetée. Le fournisseur de génération
   ne peut ni écrire ni modifier un champ de référence.
3. **Une information absente reste absente** : `missing_information`
   n'a jamais de valeur. Un champ que le fournisseur oublie devient
   `missing_information`, il n'est jamais silencieusement omis.
4. **Une sortie non conforme est rejetée avant toute persistance**
   (une relance avec la raison du rejet, puis erreur 502). Elle
   n'atteint jamais l'interface.
5. **Contenu de l'enseignant** : un booléen `edited_by_teacher`,
   orthogonal à l'étiquette. L'étiquette décrit l'origine de la
   proposition initiale ; le booléen indique qu'elle a été modifiée ou
   complétée depuis. Un champ `reference` ne se modifie pas dans la
   fiche (on corrige le document importé).
6. **Validation** : seul le statut `valide` autorise l'export PDF ;
   toute modification d'un document validé le ramène à `modifie`.
   Valider avec des informations manquantes exige une confirmation
   explicite.

## Alternatives considérées

| Option | Avantages | Inconvénients | Retenue ? |
|---|---|---|---|
| Faire confiance aux étiquettes du modèle | Simple | Une étiquette `reference` sur du texte inventé détruit toute la confiance | Non |
| Ajouter une cinquième étiquette « saisi par l'enseignant » | Explicite | Brouille le contrat des quatre étiquettes ; l'origine de la proposition initiale se perd | Non |
| **Booléen `edited_by_teacher` orthogonal** | Garde l'origine ET l'intervention humaine | Deux informations à afficher | **Oui** |

## Conséquences

- Un fournisseur de génération peut changer sans toucher à la garantie :
  elle vit dans le pipeline, pas dans le modèle.
- Les fiches générées hors-ligne contiennent beaucoup de
  `missing_information` : c'est voulu et affiché clairement.
- La vérification de fidélité ne couvre que `reference` ; une
  `deduction` ou une `ai_recommendation` reste une proposition à
  relire par l'enseignant, qui reste le décideur.

## Réversibilité

Facile pour l'interface ; coûteux pour le contrat : toute évolution des
étiquettes implique une migration des documents déjà générés.
