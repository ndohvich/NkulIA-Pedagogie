import { useState } from 'react'
import * as api from '../api/generation'
import { saveBlob } from '../api/download'
import { ProvenanceBadge } from '../components/ProvenanceBadge'
import { Alert, Button } from '../components/ui'
import { STATUS_LABEL, VOCABULARY } from './vocabulary'

/** Le gabarit garde des libellés neutres ; le vocabulaire de la filière s'applique ici. */
function labelFor(field: api.SheetField, trackSchema: api.CourseSheet['track_schema']): string {
  const words = VOCABULARY[trackSchema]
  if (field.field === 'titre_unite_apprentissage') return words.learningUnit
  if (field.field === 'titre_unite_enseignement') return words.teachingUnit
  return field.label
}

export function CourseSheetPanel({
  sheet,
  onChange,
}: {
  sheet: api.CourseSheet
  onChange: (sheet: api.CourseSheet) => void
}) {
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const [needsAcknowledgement, setNeedsAcknowledgement] = useState(false)
  const [busy, setBusy] = useState(false)

  const dirty = Object.keys(drafts).length > 0

  async function run(action: () => Promise<api.CourseSheet>, success: string) {
    setBusy(true)
    setMessage(null)
    try {
      const updated = await action()
      onChange(updated)
      setDrafts({})
      setNeedsAcknowledgement(false)
      setMessage({ tone: 'success', text: success })
    } catch (caught) {
      const text = caught instanceof Error ? caught.message : 'Action impossible.'
      setMessage({ tone: 'error', text })
      if (text.startsWith('Informations manquantes')) setNeedsAcknowledgement(true)
    } finally {
      setBusy(false)
    }
  }

  async function exportPdf() {
    setBusy(true)
    setMessage(null)
    try {
      saveBlob(await api.downloadCourseSheetPdf(sheet.id), `fiche-${sheet.id}.pdf`)
      setMessage({ tone: 'success', text: 'PDF exporté.' })
    } catch (caught) {
      setMessage({ tone: 'error', text: caught instanceof Error ? caught.message : 'Export impossible.' })
    } finally {
      setBusy(false)
    }
  }

  const save = () => run(() => api.editCourseSheet(sheet.id, drafts), 'Modifications enregistrées.')
  const validate = (acknowledge: boolean) =>
    run(() => api.validateCourseSheet(sheet.id, acknowledge), 'Fiche validée.')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-forest-deep">Fiche de cours</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          Statut : {STATUS_LABEL[sheet.status]}
        </span>
      </div>

      <dl className="space-y-4">
        {sheet.fields.map((field) => {
          const label = labelFor(field, sheet.track_schema)
          const editable = field.provenance !== 'reference'
          const current = drafts[field.field] ?? field.value ?? ''
          return (
            <div key={field.field}>
              <dt className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                {label} <ProvenanceBadge provenance={field.provenance} />
                {field.edited_by_teacher && (
                  <span className="text-xs font-normal text-slate-500">✎ modifié par vous</span>
                )}
              </dt>
              <dd className="mt-1">
                {editable ? (
                  <textarea
                    aria-label={label}
                    rows={field.field === 'objectifs' || field.field === 'prerequis' ? 2 : 4}
                    className="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
                    placeholder={field.value === null ? 'Information absente du référentiel — à compléter' : undefined}
                    value={current}
                    onChange={(e) => setDrafts((previous) => ({ ...previous, [field.field]: e.target.value }))}
                  />
                ) : (
                  <p className="rounded-md bg-stone-50 px-3 py-2 text-sm text-slate-800">{field.value}</p>
                )}
              </dd>
            </div>
          )
        })}
      </dl>

      {message && <Alert tone={message.tone}>{message.text}</Alert>}

      <div className="flex flex-wrap gap-2">
        <Button type="button" disabled={busy || !dirty} onClick={() => void save()}>
          Enregistrer les modifications
        </Button>
        {needsAcknowledgement ? (
          <Button type="button" disabled={busy} onClick={() => void validate(true)}>
            Valider malgré les informations manquantes
          </Button>
        ) : (
          <Button
            type="button"
            variant="secondary"
            disabled={busy || dirty || sheet.status === 'valide'}
            onClick={() => void validate(false)}
          >
            Valider la fiche
          </Button>
        )}
        <Button
          type="button"
          variant="secondary"
          disabled={busy || sheet.status !== 'valide'}
          title={sheet.status === 'valide' ? undefined : 'Validez la fiche pour activer l’export'}
          onClick={() => void exportPdf()}
        >
          Exporter en PDF
        </Button>
      </div>
      {sheet.status !== 'valide' && (
        <p className="text-xs text-slate-500">L'export PDF n'est possible qu'une fois la fiche validée.</p>
      )}
      {dirty && <p className="text-xs text-slate-500">Enregistrez vos modifications avant de valider.</p>}
    </div>
  )
}
