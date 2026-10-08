import { useCallback, useEffect, useState, type DragEvent, type FormEvent } from 'react'
import * as api from '../api/ingestion'
import * as generation from '../api/generation'
import { Alert, Button, Field } from '../components/ui'
import { CourseSheetPanel } from './CourseSheetPanel'
import { HierarchyPreview } from './HierarchyPreview'
import { KIND_LABEL, VOCABULARY } from './vocabulary'

interface ImportAttempt {
  key: number
  filename: string
  status: 'pending' | 'success' | 'error'
  message?: string
}

let attemptCounter = 0

const SELECT_CLASS =
  'mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest'

export function ImportScreen() {
  const [subjects, setSubjects] = useState<api.Subject[]>([])
  const [classrooms, setClassrooms] = useState<api.Classroom[]>([])
  const [classroomId, setClassroomId] = useState<number | null>(null)
  const [subjectId, setSubjectId] = useState<number | null>(null)
  const [kind, setKind] = useState<api.DocumentKind>('fiche_progression')
  const [contextError, setContextError] = useState<string | null>(null)

  const [newClassroom, setNewClassroom] = useState<{ label: string; track: api.Classroom['track'] } | null>(null)
  const [newSubject, setNewSubject] = useState<string | null>(null)

  const [attempts, setAttempts] = useState<ImportAttempt[]>([])
  const [documents, setDocuments] = useState<api.DocumentSummary[]>([])
  const [detail, setDetail] = useState<api.DocumentDetail | null>(null)
  const [dragging, setDragging] = useState(false)
  const [sheet, setSheet] = useState<generation.CourseSheet | null>(null)
  const [generating, setGenerating] = useState<string | null>(null)

  // --- Chargement initial : classes et matières -------------------------
  useEffect(() => {
    let cancelled = false
    Promise.all([api.listClassrooms(), api.listSubjects()])
      .then(([loadedClassrooms, loadedSubjects]) => {
        if (cancelled) return
        setClassrooms(loadedClassrooms)
        setSubjects(loadedSubjects)
        setClassroomId((current) => current ?? loadedClassrooms[0]?.id ?? null)
        setSubjectId((current) => current ?? loadedSubjects[0]?.id ?? null)
      })
      .catch((caught: Error) => !cancelled && setContextError(caught.message))
    return () => {
      cancelled = true
    }
  }, [])

  // --- Documents de la classe choisie ---------------------------------------
  const refreshDocuments = useCallback(async (forClassroom: number) => {
    setDocuments(await api.listDocuments(forClassroom))
  }, [])

  useEffect(() => {
    if (classroomId === null) return
    let cancelled = false
    api
      .listDocuments(classroomId)
      .then((loaded) => !cancelled && setDocuments(loaded))
      .catch((caught: Error) => !cancelled && setContextError(caught.message))
    return () => {
      cancelled = true
    }
  }, [classroomId])

  // --- Création de classe / matière -----------------------------------------
  async function handleCreateClassroom(event: FormEvent) {
    event.preventDefault()
    if (!newClassroom) return
    setContextError(null)
    try {
      const created = await api.createClassroom(newClassroom.label.trim(), newClassroom.track)
      setClassrooms((previous) => [created, ...previous])
      setClassroomId(created.id)
      setNewClassroom(null)
    } catch (caught) {
      setContextError(caught instanceof Error ? caught.message : 'Création impossible.')
    }
  }

  async function handleCreateSubject(event: FormEvent) {
    event.preventDefault()
    if (newSubject === null) return
    setContextError(null)
    try {
      const created = await api.createSubject(newSubject)
      setSubjects((previous) =>
        previous.some((s) => s.id === created.id) ? previous : [...previous, created],
      )
      setSubjectId(created.id)
      setNewSubject(null)
    } catch (caught) {
      setContextError(caught instanceof Error ? caught.message : 'Création impossible.')
    }
  }

  // --- Import ---------------------------------------------------------------
  const updateAttempt = (key: number, patch: Partial<ImportAttempt>) =>
    setAttempts((previous) => previous.map((a) => (a.key === key ? { ...a, ...patch } : a)))

  async function importFiles(files: File[]) {
    if (classroomId === null || subjectId === null) {
      setContextError('Choisissez (ou créez) une classe et une matière avant d’importer.')
      return
    }
    setContextError(null)

    for (const file of files) {
      const key = ++attemptCounter
      setAttempts((previous) => [{ key, filename: file.name, status: 'pending' }, ...previous])

      if (!file.name.toLowerCase().endsWith('.docx')) {
        updateAttempt(key, {
          status: 'error',
          message: 'Seuls les fichiers .docx sont pris en charge pour le moment.',
        })
        continue
      }

      try {
        const result = await api.importDocument(file, classroomId, subjectId, kind)
        const warningNote =
          result.warnings.length > 0 ? ` (${result.warnings.length} avertissement(s))` : ''
        updateAttempt(key, { status: 'success', message: `Importé${warningNote}` })
        await refreshDocuments(classroomId)
        setDetail(await api.getDocument(result.document_id))
      } catch (caught) {
        updateAttempt(key, {
          status: 'error',
          message: caught instanceof Error ? caught.message : 'Import impossible.',
        })
      }
    }
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)
    void importFiles(Array.from(event.dataTransfer.files))
  }

  async function generateSheet(teachingUnitId: number, title: string) {
    setContextError(null)
    setGenerating(title)
    setSheet(null)
    try {
      setSheet(await generation.createCourseSheet(teachingUnitId))
    } catch (caught) {
      setContextError(caught instanceof Error ? caught.message : 'Génération impossible.')
    } finally {
      setGenerating(null)
    }
  }

  async function openDocument(documentId: number) {
    try {
      setDetail(await api.getDocument(documentId))
    } catch (caught) {
      setContextError(caught instanceof Error ? caught.message : 'Ouverture impossible.')
    }
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-forest-deep">Import &amp; analyse</h1>
        <p className="text-sm text-slate-600">
          Déposez une fiche de progression ou un projet pédagogique : NkulIA en détecte la
          structure sans rien inventer.
        </p>
      </header>

      {contextError && <Alert tone="error">{contextError}</Alert>}

      {/* --- Contexte ------------------------------------------------------ */}
      <section className="grid gap-4 rounded-xl bg-white p-6 shadow-md sm:grid-cols-3">
        <div>
          <label htmlFor="classroom" className="block text-sm font-medium text-slate-700">
            Classe
          </label>
          <select
            id="classroom"
            className={SELECT_CLASS}
            value={classroomId ?? ''}
            onChange={(e) => setClassroomId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">— choisir —</option>
            {classrooms.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label} ({c.school_year_label})
              </option>
            ))}
          </select>
          <button
            type="button"
            className="mt-1 text-xs font-semibold text-forest underline"
            onClick={() => setNewClassroom({ label: '', track: 'generale' })}
          >
            + Nouvelle classe
          </button>
        </div>

        <div>
          <label htmlFor="subject" className="block text-sm font-medium text-slate-700">
            Matière
          </label>
          <select
            id="subject"
            className={SELECT_CLASS}
            value={subjectId ?? ''}
            onChange={(e) => setSubjectId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">— choisir —</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="mt-1 text-xs font-semibold text-forest underline"
            onClick={() => setNewSubject('')}
          >
            + Nouvelle matière
          </button>
        </div>

        <fieldset>
          <legend className="text-sm font-medium text-slate-700">Type de document</legend>
          {(Object.keys(KIND_LABEL) as api.DocumentKind[]).map((value) => (
            <label key={value} className="mt-1 flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="kind"
                checked={kind === value}
                onChange={() => setKind(value)}
              />
              {KIND_LABEL[value]}
            </label>
          ))}
        </fieldset>

        {newClassroom && (
          <form onSubmit={handleCreateClassroom} className="space-y-2 sm:col-span-3 rounded-md bg-stone-50 p-4">
            <Field
              label="Nom de la nouvelle classe"
              required
              value={newClassroom.label}
              onChange={(e) => setNewClassroom({ ...newClassroom, label: e.target.value })}
            />
            <label htmlFor="track" className="block text-sm font-medium text-slate-700">
              Filière
            </label>
            <select
              id="track"
              className={SELECT_CLASS}
              value={newClassroom.track}
              onChange={(e) =>
                setNewClassroom({ ...newClassroom, track: e.target.value as api.Classroom['track'] })
              }
            >
              <option value="generale">Générale</option>
              <option value="technique">Technique</option>
            </select>
            <div className="flex gap-2">
              <Button type="submit">Créer la classe</Button>
              <Button type="button" variant="secondary" onClick={() => setNewClassroom(null)}>
                Annuler
              </Button>
            </div>
          </form>
        )}

        {newSubject !== null && (
          <form onSubmit={handleCreateSubject} className="space-y-2 sm:col-span-3 rounded-md bg-stone-50 p-4">
            <Field
              label="Nom de la nouvelle matière"
              required
              value={newSubject}
              onChange={(e) => setNewSubject(e.target.value)}
            />
            <div className="flex gap-2">
              <Button type="submit">Créer la matière</Button>
              <Button type="button" variant="secondary" onClick={() => setNewSubject(null)}>
                Annuler
              </Button>
            </div>
          </form>
        )}
      </section>

      {/* --- Zone de dépôt ------------------------------------------------ */}
      <label
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`block cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition ${
          dragging ? 'border-forest bg-green-50' : 'border-slate-300 bg-white'
        }`}
      >
        <span className="font-semibold text-forest-deep">
          Glissez vos fichiers .docx ici, ou cliquez pour les choisir
        </span>
        <input
          type="file"
          accept=".docx"
          multiple
          className="sr-only"
          aria-label="Choisir des fichiers .docx"
          onChange={(e) => {
            void importFiles(Array.from(e.target.files ?? []))
            e.target.value = ''
          }}
        />
      </label>

      {/* --- Statut des imports de la session ------------------------------ */}
      {attempts.length > 0 && (
        <ul aria-label="Statut des imports" className="space-y-2">
          {attempts.map((attempt) => (
            <li key={attempt.key}>
              {attempt.status === 'pending' && <Alert tone="info">{attempt.filename} : analyse en cours…</Alert>}
              {attempt.status === 'success' && (
                <Alert tone="success">
                  {attempt.filename} : {attempt.message}
                </Alert>
              )}
              {attempt.status === 'error' && (
                <Alert tone="error">
                  {attempt.filename} : échec — {attempt.message}
                </Alert>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* --- Documents importés -------------------------------------------- */}
      {classroomId !== null && (
        <section className="rounded-xl bg-white p-6 shadow-md">
          <h2 className="mb-3 text-lg font-bold text-forest-deep">Documents importés</h2>
          {documents.length === 0 ? (
            <p className="text-sm text-slate-500">Aucun document pour cette classe.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {documents.map((document) => (
                <li key={document.id} className="flex items-center justify-between gap-4 py-2 text-sm">
                  <span>
                    <strong>{document.filename}</strong>
                    <span className="ml-2 text-slate-500">
                      {KIND_LABEL[document.kind]} · {document.module_count} modules ·{' '}
                      {document.learning_unit_count} {VOCABULARY[document.track_schema].learningUnits} ·{' '}
                      {document.teaching_unit_count} unités fines
                      {document.warning_count > 0 && ` · ${document.warning_count} avertissement(s)`}
                    </span>
                  </span>
                  <Button variant="secondary" onClick={() => void openDocument(document.id)}>
                    Voir la structure
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {detail && (
        <section className="rounded-xl bg-white p-6 shadow-md" aria-label="Structure détectée">
          <HierarchyPreview
            document={detail}
            onGenerate={(unitId, title) => void generateSheet(unitId, title)}
          />
        </section>
      )}

      {generating && <Alert tone="info">Génération de la fiche « {generating} »…</Alert>}

      {sheet && (
        <section className="rounded-xl bg-white p-6 shadow-md" aria-label="Fiche de cours">
          <CourseSheetPanel sheet={sheet} onChange={setSheet} />
        </section>
      )}
    </div>
  )
}
