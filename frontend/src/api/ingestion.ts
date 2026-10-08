import { apiRequest } from './client'

export type DocumentKind = 'fiche_progression' | 'projet_pedagogique'
export type TrackSchema = 'ua_ue' | 'chapitre_lecon'

export interface Subject {
  id: number
  name: string
}

export interface Classroom {
  id: number
  label: string
  track: 'generale' | 'technique'
  school_year_label: string
}

export interface DocumentSummary {
  id: number
  filename: string
  kind: DocumentKind
  track_schema: TrackSchema
  imported_at: string
  module_count: number
  learning_unit_count: number
  teaching_unit_count: number
  warning_count: number
}

export interface TeachingUnit {
  id: number
  number: string
  title: string
  digitalized: boolean | null
  actions: string | null
  essential_knowledge: string | null
  duration_label: string | null
  session_type: string | null
}

export interface LearningUnit {
  id: number
  number: string
  title: string
  teaching_units: TeachingUnit[]
}

export interface Module {
  id: number
  number: string
  title: string
  learning_units: LearningUnit[]
}

export interface DocumentDetail extends DocumentSummary {
  modules: Module[]
  warnings: string[]
}

export const listSubjects = () => apiRequest<Subject[]>('/context/subjects')

export const createSubject = (name: string) =>
  apiRequest<Subject>('/context/subjects', { method: 'POST', json: { name } })

export const listClassrooms = () => apiRequest<Classroom[]>('/context/classrooms')

export const createClassroom = (label: string, track: Classroom['track']) =>
  apiRequest<Classroom>('/context/classrooms', { method: 'POST', json: { label, track } })

export const listDocuments = (classroomId: number) =>
  apiRequest<DocumentSummary[]>(`/ingestion/documents?classroom_id=${classroomId}`)

export const getDocument = (documentId: number) =>
  apiRequest<DocumentDetail>(`/ingestion/documents/${documentId}`)

export function importDocument(
  file: File,
  classroomId: number,
  subjectId: number,
  kind: DocumentKind,
) {
  const form = new FormData()
  form.append('classroom_id', String(classroomId))
  form.append('subject_id', String(subjectId))
  form.append('kind', kind)
  form.append('file', file)
  return apiRequest<{ document_id: number; filename: string; warnings: string[] }>(
    '/ingestion/import',
    { method: 'POST', form },
  )
}
