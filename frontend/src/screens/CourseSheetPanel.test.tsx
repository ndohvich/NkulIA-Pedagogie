import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import { mockApi, teacher, type MockCall } from '../testUtils'

const field = (name: string, label: string, value: string | null, provenance: string, extra = {}) => ({
  field: name, label, value, provenance, source_ref: provenance === 'reference' ? 'f.docx#x' : null,
  edited_by_teacher: false, ...extra,
})

const sheet = (status: string, objectifs: string | null = null) => ({
  id: 9, teaching_unit_id: 1, status, provider_name: 'offline', validated_at: null, track_schema: 'ua_ue',
  fields: [
    field('titre_module', 'Module', 'Environnement numérique', 'reference'),
    field('titre_unite_enseignement', "Unité d'enseignement / Leçon", 'Les périphériques', 'reference'),
    field('objectifs', 'Objectifs', objectifs, objectifs ? 'missing_information' : 'missing_information',
      { edited_by_teacher: objectifs !== null }),
    field('prerequis', 'Prérequis', 'Avoir étudié les unités qui précèdent : X.', 'deduction'),
  ],
})

const detail = {
  id: 42, filename: 'f.docx', kind: 'fiche_progression', track_schema: 'ua_ue', imported_at: '2026-10-02T08:00:00Z',
  module_count: 1, learning_unit_count: 1, teaching_unit_count: 1, warning_count: 0, warnings: [],
  modules: [{ id: 1, number: '1', title: 'M', learning_units: [{ id: 1, number: '1', title: 'U', teaching_units: [
    { id: 1, number: '1', title: 'Les périphériques', digitalized: true, actions: null, essential_knowledge: null, duration_label: null, session_type: null },
  ] }] }],
}

function server(extra: (call: MockCall) => { status?: number; json?: unknown } | undefined) {
  return (call: MockCall) => {
    if (call.url.endsWith('/me')) return { json: teacher }
    if (call.url.endsWith('/context/classrooms')) return { json: [{ id: 7, label: 'Seconde', track: 'generale', school_year_label: '2026-2027' }] }
    if (call.url.endsWith('/context/subjects')) return { json: [{ id: 3, name: 'Informatique' }] }
    if (call.url.includes('/ingestion/documents?')) return { json: [{ ...detail }] }
    if (call.url.endsWith('/ingestion/documents/42')) return { json: detail }
    return extra(call)
  }
}

beforeEach(() => window.localStorage.setItem('nkulia.token', 'tok'))
afterEach(() => { window.localStorage.clear(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

async function openSheet(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button', { name: 'Voir la structure' }))
  await user.click(await screen.findByRole('button', { name: /Générer une fiche : Les périphériques/ }))
  return screen.findByRole('region', { name: 'Fiche de cours' })
}

describe('Fiche de cours générée (issue #13)', () => {
  it('affiche chaque champ avec son badge de provenance et verrouille les références', async () => {
    mockApi(server((call) => (call.url.endsWith('/generation/course-sheets') ? { status: 201, json: sheet('propose') } : undefined)))
    const user = userEvent.setup()
    render(<App />)
    const panel = await openSheet(user)

    expect(within(panel).getByText('Statut : Proposé')).toBeInTheDocument()
    expect(within(panel).getByText('Unité d\'Enseignement')).toBeInTheDocument() // vocabulaire UA/UE appliqué
    expect(within(panel).getAllByText('Référence')).toHaveLength(2)
    expect(within(panel).getByText('Déduction')).toBeInTheDocument()
    expect(within(panel).getByText('Information manquante')).toBeInTheDocument()
    expect(within(panel).queryByRole('textbox', { name: 'Module' })).not.toBeInTheDocument()
    expect(within(panel).getByRole('textbox', { name: 'Objectifs' })).toHaveAttribute('placeholder', expect.stringContaining('à compléter'))
  })

  it('enregistre une modification puis valide après confirmation des manques', async () => {
    const calls = mockApi(server((call) => {
      if (call.url.endsWith('/generation/course-sheets')) return { status: 201, json: sheet('propose') }
      if (call.method === 'PATCH') return { json: sheet('modifie', 'Identifier les périphériques') }
      if (call.url.endsWith('/validate')) {
        const acknowledged = (call.body as { acknowledge_missing: boolean }).acknowledge_missing
        return acknowledged
          ? { json: sheet('valide', 'Identifier les périphériques') }
          : { status: 409, json: { detail: 'Informations manquantes : Situation-problème. Complétez-les ou confirmez.' } }
      }
      return undefined
    }))
    const user = userEvent.setup()
    render(<App />)
    const panel = await openSheet(user)

    await user.type(within(panel).getByRole('textbox', { name: 'Objectifs' }), 'Identifier les périphériques')
    await user.click(within(panel).getByRole('button', { name: 'Enregistrer les modifications' }))
    expect(await within(panel).findByText('Statut : Modifié')).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'PATCH')?.body).toEqual({ fields: { objectifs: 'Identifier les périphériques' } })
    expect(within(panel).getByText('✎ modifié par vous')).toBeInTheDocument()

    await user.click(within(panel).getByRole('button', { name: 'Valider la fiche' }))
    expect(await within(panel).findByRole('alert')).toHaveTextContent('Informations manquantes')

    await user.click(within(panel).getByRole('button', { name: 'Valider malgré les informations manquantes' }))
    expect(await within(panel).findByText('Statut : Validé')).toBeInTheDocument()
  })

  it("n'active l'export PDF qu'une fois la fiche validée, puis télécharge le fichier", async () => {
    const created = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    vi.stubGlobal('URL', { ...URL, createObjectURL: () => 'blob:x', revokeObjectURL: created })
    const calls = mockApi(server((call) => {
      if (call.url.endsWith('/generation/course-sheets')) return { status: 201, json: sheet('propose') }
      if (call.url.endsWith('/validate')) return { json: sheet('valide', 'Un objectif') }
      return undefined
    }))
    // Réponse binaire pour le PDF : on complète le faux fetch existant.
    const baseFetch = globalThis.fetch
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) =>
      String(url).endsWith('/pdf')
        ? ({ ok: true, status: 200, blob: async () => new Blob(['%PDF-']) } as Response)
        : baseFetch(url, init)))

    const user = userEvent.setup()
    render(<App />)
    const panel = await openSheet(user)

    expect(within(panel).getByRole('button', { name: 'Exporter en PDF' })).toBeDisabled()
    expect(within(panel).getByText(/qu'une fois la fiche validée/)).toBeInTheDocument()

    await user.click(within(panel).getByRole('button', { name: 'Valider la fiche' }))
    const exportButton = within(panel).getByRole('button', { name: 'Exporter en PDF' })
    await vi.waitFor(() => expect(exportButton).toBeEnabled())
    await user.click(exportButton)

    expect(await within(panel).findByText('PDF exporté.')).toBeInTheDocument()
    expect(created).toHaveBeenCalled()
    void calls
  })

  it("affiche le refus quand la sortie du générateur est rejetée", async () => {
    mockApi(server((call) => call.url.endsWith('/generation/course-sheets')
      ? { status: 502, json: { detail: 'Sortie rejetée après 2 tentatives : champ sans étiquette.' } }
      : undefined))
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('button', { name: 'Voir la structure' }))
    await user.click(await screen.findByRole('button', { name: /Générer une fiche/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Sortie rejetée')
    expect(screen.queryByRole('region', { name: 'Fiche de cours' })).not.toBeInTheDocument()
  })
})
