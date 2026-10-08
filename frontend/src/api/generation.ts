import { apiRequest } from './client'
import type { Provenance } from '../components/ProvenanceBadge'

export type SheetStatus = 'brouillon' | 'analyse' | 'propose' | 'modifie' | 'valide'

export interface SheetField {
  field: string
  label: string
  value: string | null
  provenance: Provenance
  source_ref: string | null
  edited_by_teacher: boolean
}

export interface CourseSheet {
  id: number
  teaching_unit_id: number
  status: SheetStatus
  provider_name: string
  validated_at: string | null
  track_schema: 'ua_ue' | 'chapitre_lecon'
  fields: SheetField[]
}

export const createCourseSheet = (teachingUnitId: number) =>
  apiRequest<CourseSheet>('/generation/course-sheets', {
    method: 'POST',
    json: { teaching_unit_id: teachingUnitId },
  })

export const editCourseSheet = (id: number, fields: Record<string, string>) =>
  apiRequest<CourseSheet>(`/generation/documents/${id}`, { method: 'PATCH', json: { fields } })

export const validateCourseSheet = (id: number, acknowledgeMissing: boolean) =>
  apiRequest<CourseSheet>(`/generation/documents/${id}/validate`, {
    method: 'POST',
    json: { acknowledge_missing: acknowledgeMissing },
  })

export const downloadCourseSheetPdf = (id: number) =>
  apiRequest<Blob>(`/generation/documents/${id}/pdf`, { responseType: 'blob' })
