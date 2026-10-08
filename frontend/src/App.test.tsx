import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { mockApi, teacher } from './testUtils'

beforeEach(() => window.localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('Parcours inscription → connexion → profil (issue #8)', () => {
  it("affiche la connexion quand aucune session n'existe", () => {
    mockApi(() => undefined)
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
  })

  it('connecte un enseignant puis affiche son profil pré-rempli', async () => {
    const calls = mockApi((call) =>
      call.url.endsWith('/auth/login') ? { json: { token: 'tok-123', teacher } } : undefined,
    )
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('Adresse email'), 'jules@exemple.cm')
    await user.type(screen.getByLabelText('Mot de passe'), 'MotDePasse123')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))

    await user.click(await screen.findByRole('button', { name: 'Profil' }))
    expect(await screen.findByRole('heading', { name: 'Mon profil' })).toBeInTheDocument()
    expect(screen.getByLabelText('Nom')).toHaveValue('Yannick')
    expect(screen.getByLabelText('Établissement')).toHaveValue("Lycée Technique d'Ébolowa")
    expect(calls[0].body).toEqual({ email: 'jules@exemple.cm', password: 'MotDePasse123' })
    expect(window.localStorage.getItem('nkulia.token')).toBe('tok-123')
  })

  it("affiche l'erreur de l'API quand le mot de passe est faux", async () => {
    mockApi(() => ({ status: 401, json: { detail: 'Email ou mot de passe incorrect.' } }))
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('Adresse email'), 'jules@exemple.cm')
    await user.type(screen.getByLabelText('Mot de passe'), 'mauvais')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou mot de passe incorrect.')
  })

  it("refuse une inscription dont le mot de passe n'a pas de chiffre, sans appeler l'API", async () => {
    const calls = mockApi(() => undefined)
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Créer un compte' }))
    await user.type(screen.getByLabelText('Nom'), 'Yannick')
    await user.type(screen.getByLabelText('Prénom'), 'Jules')
    await user.type(screen.getByLabelText('Adresse email'), 'jules@exemple.cm')
    await user.type(screen.getByLabelText('Mot de passe'), 'sansaucunchiffre')
    await user.type(screen.getByLabelText('Confirmer le mot de passe'), 'sansaucunchiffre')
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('au moins un chiffre')
    expect(calls).toHaveLength(0)
  })

  it('inscrit un enseignant et ouvre directement son profil', async () => {
    const calls = mockApi((call) =>
      call.url.endsWith('/auth/register') ? { status: 201, json: { token: 't', teacher } } : undefined,
    )
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Créer un compte' }))
    await user.type(screen.getByLabelText('Nom'), 'Yannick')
    await user.type(screen.getByLabelText('Prénom'), 'Jules')
    await user.type(screen.getByLabelText('Adresse email'), 'jules@exemple.cm')
    await user.type(screen.getByLabelText('Mot de passe'), 'MotDePasse123')
    await user.type(screen.getByLabelText('Confirmer le mot de passe'), 'MotDePasse123')
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(await screen.findByRole('heading', { name: 'Import & analyse' })).toBeInTheDocument()
    expect(calls[0].body).toMatchObject({ email: 'jules@exemple.cm', last_name: 'Yannick' })
  })

  it('enregistre une modification du profil via PATCH /me', async () => {
    window.localStorage.setItem('nkulia.token', 'tok')
    const calls = mockApi((call) => {
      if (call.url.endsWith('/me') && call.method === 'GET') return { json: teacher }
      if (call.url.endsWith('/me') && call.method === 'PATCH')
        return { json: { ...teacher, grade: 'PLEG' } }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)

    await user.click(await screen.findByRole('button', { name: 'Profil' }))
    await screen.findByRole('heading', { name: 'Mon profil' })
    await user.type(screen.getByLabelText('Grade'), 'PLEG')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Profil enregistré.')
    const patch = calls.find((c) => c.method === 'PATCH')
    expect(patch?.body).toMatchObject({ grade: 'PLEG' })
    expect(patch?.headers['Authorization']).toBe('Bearer tok')
  })

  it('retourne à la connexion quand la session stockée est expirée', async () => {
    window.localStorage.setItem('nkulia.token', 'expire')
    mockApi(() => ({ status: 401, json: { detail: 'Authentification requise ou expirée.' } }))
    render(<App />)

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Connexion' })).toBeInTheDocument(),
    )
    expect(window.localStorage.getItem('nkulia.token')).toBeNull()
  })

  it('se déconnecte et oublie le jeton', async () => {
    window.localStorage.setItem('nkulia.token', 'tok')
    mockApi((call) => {
      if (call.url.endsWith('/me')) return { json: teacher }
      if (call.url.endsWith('/auth/logout')) return { status: 204 }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)

    await screen.findByRole('heading', { name: 'Import & analyse' })
    await user.click(screen.getByRole('button', { name: 'Se déconnecter' }))

    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
    expect(window.localStorage.getItem('nkulia.token')).toBeNull()
  })
})
