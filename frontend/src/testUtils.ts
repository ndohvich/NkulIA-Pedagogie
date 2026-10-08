import { vi } from 'vitest'

export interface MockCall {
  url: string
  method: string
  body: unknown
  headers: Record<string, string>
}

type Responder = (call: MockCall) => { status?: number; json?: unknown } | undefined

/** Remplace `fetch` par un faux serveur et mémorise les appels reçus. */
export function mockApi(responder: Responder): MockCall[] {
  const calls: MockCall[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init: RequestInit = {}) => {
      const call: MockCall = {
        url,
        method: init.method ?? 'GET',
        body: typeof init.body === 'string' ? JSON.parse(init.body) : init.body,
        headers: (init.headers ?? {}) as Record<string, string>,
      }
      calls.push(call)
      // Par défaut, les listes de contexte (classes, matières, documents) sont vides.
      const emptyList = /\/context\/|\/ingestion\/documents\?/.test(call.url) && call.method === 'GET'
      const reply =
        responder(call) ??
        (emptyList ? { json: [] } : { status: 404, json: { detail: 'Introuvable' } })
      const status = reply.status ?? 200
      return {
        ok: status >= 200 && status < 300,
        status,
        json: async () => reply.json,
      } as Response
    }),
  )
  return calls
}

export const teacher = {
  id: 1,
  email: 'jules@exemple.cm',
  last_name: 'Yannick',
  first_name: 'Jules',
  subject_taught: 'Informatique',
  specialty: null,
  grade: null,
  function: null,
  institution_name: "Lycée Technique d'Ébolowa",
}
