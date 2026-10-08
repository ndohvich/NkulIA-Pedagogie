import { useState, type FormEvent } from 'react'
import { Alert, Button, Card, Field } from '../components/ui'
import { useAuth } from '../auth/AuthContext'

export function LoginScreen({ onGoToRegister }: { onGoToRegister: () => void }) {
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await signIn(email.trim(), password)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Connexion impossible.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Connexion">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Adresse email" type="email" required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field label="Mot de passe" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <Alert tone="error">{error}</Alert>}
        <Button type="submit" disabled={busy}>
          {busy ? 'Connexion…' : 'Se connecter'}
        </Button>
      </form>
      <p className="mt-6 text-sm text-slate-600">
        Pas encore de compte ?{' '}
        <button type="button" onClick={onGoToRegister} className="font-semibold text-forest underline">
          Créer un compte
        </button>
      </p>
    </Card>
  )
}
