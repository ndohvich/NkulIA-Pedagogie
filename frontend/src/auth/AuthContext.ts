import { createContext, useContext } from 'react'
import type { ProfileUpdate, RegisterPayload, TeacherProfile } from '../api/auth'

export interface AuthState {
  /** `loading` : vérification d'un jeton déjà stocké au démarrage. */
  status: 'loading' | 'anonymous' | 'authenticated'
  teacher: TeacherProfile | null
  signIn: (email: string, password: string) => Promise<void>
  signUp: (payload: RegisterPayload) => Promise<void>
  signOut: () => Promise<void>
  saveProfile: (update: ProfileUpdate) => Promise<void>
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const value = useContext(AuthContext)
  if (value === null) throw new Error('useAuth doit être utilisé sous <AuthProvider>.')
  return value
}
