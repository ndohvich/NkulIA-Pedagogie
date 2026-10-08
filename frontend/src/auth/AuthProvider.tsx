import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { getToken, setToken, setUnauthorizedHandler } from '../api/client'
import { AuthContext, type AuthState } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthState['status']>(() =>
    getToken() ? 'loading' : 'anonymous',
  )
  const [teacher, setTeacher] = useState<authApi.TeacherProfile | null>(null)

  const clearSession = useCallback(() => {
    setToken(null)
    setTeacher(null)
    setStatus('anonymous')
  }, [])

  // Session expirée détectée par n'importe quel appel : retour à la connexion.
  useEffect(() => {
    setUnauthorizedHandler(clearSession)
    return () => setUnauthorizedHandler(null)
  }, [clearSession])

  // Au démarrage, un jeton stocké est revérifié auprès de l'API.
  useEffect(() => {
    if (status !== 'loading') return
    let cancelled = false
    authApi
      .fetchMe()
      .then((profile) => {
        if (cancelled) return
        setTeacher(profile)
        setStatus('authenticated')
      })
      .catch(() => {
        if (!cancelled) clearSession()
      })
    return () => {
      cancelled = true
    }
  }, [status, clearSession])

  const startSession = useCallback((session: authApi.SessionOut) => {
    setToken(session.token)
    setTeacher(session.teacher)
    setStatus('authenticated')
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      status,
      teacher,
      signIn: async (email, password) => startSession(await authApi.login(email, password)),
      signUp: async (payload) => startSession(await authApi.register(payload)),
      signOut: async () => {
        try {
          await authApi.logout()
        } finally {
          clearSession() // même si l'API est injoignable, on quitte la session locale
        }
      },
      saveProfile: async (update) => setTeacher(await authApi.updateMe(update)),
    }),
    [status, teacher, startSession, clearSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
