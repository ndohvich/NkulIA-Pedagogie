import { apiRequest } from './client'

export interface TeacherProfile {
  id: number
  email: string
  last_name: string
  first_name: string
  subject_taught: string | null
  specialty: string | null
  grade: string | null
  function: string | null
  institution_name: string | null
}

export interface SessionOut {
  token: string
  teacher: TeacherProfile
}

export interface RegisterPayload {
  email: string
  password: string
  last_name: string
  first_name: string
  institution_name?: string
  subject_taught?: string
}

export type ProfileUpdate = Partial<
  Pick<
    TeacherProfile,
    | 'last_name'
    | 'first_name'
    | 'subject_taught'
    | 'specialty'
    | 'grade'
    | 'function'
    | 'institution_name'
  >
>

export const register = (payload: RegisterPayload) =>
  apiRequest<SessionOut>('/auth/register', { method: 'POST', json: payload, auth: false })

export const login = (email: string, password: string) =>
  apiRequest<SessionOut>('/auth/login', { method: 'POST', json: { email, password }, auth: false })

export const logout = () => apiRequest<void>('/auth/logout', { method: 'POST' })

export const fetchMe = () => apiRequest<TeacherProfile>('/me')

export const updateMe = (payload: ProfileUpdate) =>
  apiRequest<TeacherProfile>('/me', { method: 'PATCH', json: payload })
