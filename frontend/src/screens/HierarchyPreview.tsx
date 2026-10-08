import type { DocumentDetail } from '../api/ingestion'
import { ProvenanceBadge } from '../components/ProvenanceBadge'
import { Alert, Button } from '../components/ui'
import { VOCABULARY } from './vocabulary'

function Digitalisation({ value }: { value: boolean | null }) {
  // Strictement binaire dans le référentiel (OUI/NON) ; `null` = absente ou
  // illisible, jamais devinée — voir backend/app/db/models.py, TeachingUnit.
  if (value === null) return <ProvenanceBadge provenance="missing_information" />
  return (
    <span className={value ? 'font-semibold text-forest' : 'font-semibold text-laterite'}>
      {value ? 'OUI' : 'NON'}
    </span>
  )
}

/** Aperçu de la hiérarchie détectée : Module → UA/Chapitre → UE/Leçon (« fil pédagogique »). */
export function HierarchyPreview({
  document,
  onGenerate,
}: {
  document: DocumentDetail
  onGenerate?: (teachingUnitId: number, title: string) => void
}) {
  const words = VOCABULARY[document.track_schema]
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        Structure extraite de <strong>{document.filename}</strong> <ProvenanceBadge provenance="reference" />
      </p>

      {document.warnings.length > 0 && (
        <Alert tone="info">
          {document.warnings.length} ligne(s) ignorée(s) ou à vérifier :
          <ul className="mt-1 list-inside list-disc">
            {document.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {document.modules.map((module) => (
        <section key={module.id} className="rounded-lg border border-slate-200 p-4">
          <h3 className="font-bold text-forest-deep">
            Module {module.number} — {module.title}
          </h3>
          {module.learning_units.map((learningUnit) => (
            <div key={learningUnit.id} className="mt-3 border-l-2 border-gold pl-3">
              <p className="font-semibold text-slate-800">
                {words.learningUnit} {learningUnit.number} — {learningUnit.title}
              </p>
              <ul className="mt-1 space-y-1 text-sm">
                {learningUnit.teaching_units.map((teachingUnit) => (
                  <li key={teachingUnit.id} className="flex items-baseline justify-between gap-4">
                    <span>
                      <span className="text-slate-500">{words.teachingUnit} {teachingUnit.number}</span>{' '}
                      {teachingUnit.title}
                    </span>
                    <span className="flex shrink-0 items-center gap-3 text-xs text-slate-500">
                      <span>
                        Digitalisation : <Digitalisation value={teachingUnit.digitalized} />
                      </span>
                      {onGenerate && (
                        <Button
                          type="button"
                          variant="secondary"
                          aria-label={`Générer une fiche : ${teachingUnit.title}`}
                          onClick={() => onGenerate(teachingUnit.id, teachingUnit.title)}
                        >
                          Générer une fiche
                        </Button>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      ))}
    </div>
  )
}
