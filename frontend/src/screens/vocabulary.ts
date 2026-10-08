import type { SheetStatus } from '../api/generation'
import type { TrackSchema } from '../api/ingestion'

/**
 * Le vocabulaire d'une filière est une DONNÉE de configuration, jamais
 * un nom de colonne ou de table (docs/adr/0003, principe n°4) : l'API
 * renvoie une structure neutre, c'est ici qu'on choisit les mots.
 */
export const VOCABULARY: Record<
  TrackSchema,
  { learningUnit: string; teachingUnit: string; learningUnits: string }
> = {
  ua_ue: {
    learningUnit: "Unité d'Apprentissage",
    teachingUnit: "Unité d'Enseignement",
    learningUnits: "unités d'apprentissage",
  },
  chapitre_lecon: { learningUnit: 'Chapitre', teachingUnit: 'Leçon', learningUnits: 'chapitres' },
}

export const KIND_LABEL = {
  fiche_progression: 'Fiche de progression',
  projet_pedagogique: 'Projet pédagogique',
} as const

export const STATUS_LABEL: Record<SheetStatus, string> = {
  brouillon: 'Brouillon',
  analyse: 'Analysé',
  propose: 'Proposé',
  modifie: 'Modifié',
  valide: 'Validé',
}
