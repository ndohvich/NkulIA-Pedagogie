/**
 * Client HTTP minimal vers l'API locale NkulIA.
 *
 * Les chemins sont RELATIFS (`/api/v1/...`) : en production l'interface
 * est servie par FastAPI lui-même (voir desktop/main.py), donc même
 * origine, aucun CORS. En développement, le proxy de Vite
 * (vite.config.ts) renvoie `/api` vers 127.0.0.1:8000.
 */

const TOKEN_KEY = 'nkulia.token'
export const API_PREFIX = '/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token === null) window.localStorage.removeItem(TOKEN_KEY)
    else window.localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Stockage indisponible : la session ne survivra pas au rechargement,
    // mais l'application reste utilisable.
  }
}

let onUnauthorized: (() => void) | null = null

/** Appelé quand l'API répond 401 à une requête authentifiée (session expirée). */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

type FastApiDetail = string | { msg?: string }[] | undefined

function messageFromDetail(detail: FastApiDetail, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => item.msg?.replace(/^Value error, /, '') ?? '')
      .filter(Boolean)
      .join(' ')
  }
  return fallback
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  json?: unknown
  form?: FormData
  /** Faux pour les routes publiques (connexion, inscription). */
  auth?: boolean
  /** `blob` pour télécharger un fichier (ex. PDF) au lieu de lire du JSON. */
  responseType?: 'json' | 'blob'
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', json, form, auth = true, responseType = 'json' } = options
  const headers: Record<string, string> = {}
  let body: BodyInit | undefined

  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (form !== undefined) {
    body = form // le navigateur fixe lui-même le Content-Type multipart
  }

  const token = getToken()
  if (auth && token) headers['Authorization'] = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${API_PREFIX}${path}`, { method, headers, body })
  } catch {
    throw new ApiError(0, "Impossible de joindre l'application locale. Relancez NkulIA.")
  }

  if (response.status === 401 && auth && token) onUnauthorized?.()

  if (!response.ok) {
    let detail: FastApiDetail
    try {
      detail = ((await response.json()) as { detail?: FastApiDetail }).detail
    } catch {
      detail = undefined
    }
    throw new ApiError(
      response.status,
      messageFromDetail(detail, `Erreur ${response.status} inattendue.`),
    )
  }

  if (response.status === 204) return undefined as T
  if (responseType === 'blob') return (await response.blob()) as T
  return (await response.json()) as T
}
