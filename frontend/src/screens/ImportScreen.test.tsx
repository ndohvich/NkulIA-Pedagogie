import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import { mockApi, teacher, type MockCall } from '../testUtils'

const classroom = { id: 7, label: 'Seconde C', track: 'generale', school_year_label: '2026-2027' }
const subject = { id: 3, name: 'Informatique' }

const summary = {
  id: 42,
  filename: 'fiche_progression_seconde.docx',
  kind: 'fiche_progression',
  track_schema: 'ua_ue',
  imported_at: '2026-10-02T08:00:00Z',
  module_count: 1,
  learning_unit_count: 1,
  teaching_unit_count: 2,
  warning_count: 1,
}

const detail = {
  ...summary,
  warnings: ['Ligne ÉVALUATION DE FIN DE TRIMESTRE ignorée'],
  modules: [
    {
      id: 1,
      number: '1',
      title: 'Environnement numérique',
      learning_units: [
        {
          id: 1,
          number: '1',
          title: 'Le matériel informatique',
          teaching_units: [
            { id: 1, number: '1', title: 'Les périphériques', digitalized: true, actions: null, essential_knowledge: null, duration_label: null, session_type: null },
            { id: 2, number: '2', title: 'Le réseau', digitalized: null, actions: null, essential_knowledge: null, duration_label: null, session_type: null },
          ],
        },
      ],
    },
  ],
}

function server(importReply: { status: number; json: unknown }) {
  return (call: MockCall) => {
    if (call.url.endsWith('/me')) return { json: teacher }
    if (call.url.endsWith('/context/classrooms') && call.method === 'GET') return { json: [classroom] }
    if (call.url.endsWith('/context/subjects') && call.method === 'GET') return { json: [subject] }
    if (call.url.includes('/ingestion/documents?')) return { json: [] }
    if (call.url.endsWith('/ingestion/import')) return importReply
    if (call.url.endsWith('/ingestion/documents/42')) return { json: detail }
    return undefined
  }
}

beforeEach(() => window.localStorage.setItem('nkulia.token', 'tok'))
afterEach(() => {
  window.localStorage.clear()
  vi.unstubAllGlobals()
})

const docx = () => new File(['x'], 'fiche_progression_seconde.docx')

describe('Écran Import & analyse (issue #11)', () => {
  it('importe un fichier et montre la hiérarchie détectée sans lire les logs', async () => {
    const calls = mockApi(server({ status: 201, json: { document_id: 42, filename: summary.filename, warnings: detail.warnings } }))
    const user = userEvent.setup()
    render(<App />)

    await waitFor(() => expect(screen.getByLabelText('Classe')).toHaveValue('7'))
    await user.upload(screen.getByLabelText('Choisir des fichiers .docx'), docx())

    const status = await screen.findByRole('list', { name: 'Statut des imports' })
    expect(within(status).getByRole('status')).toHaveTextContent('Importé (1 avertissement(s))')

    const preview = await screen.findByRole('region', { name: 'Structure détectée' })
    expect(within(preview).getByText(/Module 1 — Environnement numérique/)).toBeInTheDocument()
    expect(within(preview).getByText(/Unité d'Apprentissage 1 — Le matériel informatique/)).toBeInTheDocument()
    expect(within(preview).getByText('OUI')).toBeInTheDocument()
    expect(within(preview).getByText('Information manquante')).toBeInTheDocument()
    expect(within(preview).getByText(/ÉVALUATION DE FIN DE TRIMESTRE/)).toBeInTheDocument()

    const upload = calls.find((c) => c.url.endsWith('/ingestion/import'))
    const form = upload?.body as FormData
    expect(form.get('classroom_id')).toBe('7')
    expect(form.get('subject_id')).toBe('3')
    expect(form.get('kind')).toBe('fiche_progression')
  })

  it("montre clairement un import en échec avec le message de l'API", async () => {
    mockApi(server({ status: 422, json: { detail: 'Colonne « Module » introuvable dans le tableau.' } }))
    const user = userEvent.setup()
    render(<App />)

    await waitFor(() => expect(screen.getByLabelText('Classe')).toHaveValue('7'))
    await user.upload(screen.getByLabelText('Choisir des fichiers .docx'), docx())

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('échec')
    expect(alert).toHaveTextContent('Colonne « Module » introuvable')
    expect(screen.queryByRole('region', { name: 'Structure détectée' })).not.toBeInTheDocument()
  })

  it('refuse un fichier non .docx sans appeler le serveur', async () => {
    const calls = mockApi(server({ status: 201, json: {} }))
    // `applyAccept: false` : on simule un dépôt par glisser-déposer, qui ignore l'attribut accept.
    const user = userEvent.setup({ applyAccept: false })
    render(<App />)

    await waitFor(() => expect(screen.getByLabelText('Classe')).toHaveValue('7'))
    await user.upload(screen.getByLabelText('Choisir des fichiers .docx'), new File(['x'], 'notes.pdf'))

    expect(await screen.findByRole('alert')).toHaveTextContent('Seuls les fichiers .docx')
    expect(calls.some((c) => c.url.endsWith('/ingestion/import'))).toBe(false)
  })

  it('demande de choisir une classe et une matière avant tout import', async () => {
    mockApi((call) => (call.url.endsWith('/me') ? { json: teacher } : undefined))
    const user = userEvent.setup()
    render(<App />)

    await screen.findByRole('heading', { name: 'Import & analyse' })
    await user.upload(screen.getByLabelText('Choisir des fichiers .docx'), docx())

    expect(await screen.findByRole('alert')).toHaveTextContent('une classe et une matière')
  })

  it('crée une classe depuis l’écran', async () => {
    const calls = mockApi((call) => {
      if (call.url.endsWith('/me')) return { json: teacher }
      if (call.url.endsWith('/context/classrooms') && call.method === 'POST')
        return { status: 201, json: classroom }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)

    await user.click(await screen.findByRole('button', { name: '+ Nouvelle classe' }))
    await user.type(screen.getByLabelText('Nom de la nouvelle classe'), 'Seconde C')
    await user.selectOptions(screen.getByLabelText('Filière'), 'technique')
    await user.click(screen.getByRole('button', { name: 'Créer la classe' }))

    await waitFor(() => expect(screen.getByLabelText('Classe')).toHaveValue('7'))
    const post = calls.find((c) => c.url.endsWith('/context/classrooms') && c.method === 'POST')
    expect(post?.body).toEqual({ label: 'Seconde C', track: 'technique' })
  })
})
