import { useState, type FormEvent } from 'react'
import { Alert, Button, Card, Field } from '../components/ui'
import { useAuth } from '../auth/AuthContext'
import { passwordProblem } from '../auth/passwordRules'

export function RegisterScreen({ onGoToLogin }: { onGoToLogin: () => void }) {
  const { signUp } = useAuth()
  const [form, setForm] = useState({
    last_name: '',
    first_name: '',
    email: '',
    password: '',
    confirm: '',
    institution_name: '',
    subject_taught: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((previous) => ({ ...previous, [key]: e.target.value }))

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    const problem = passwordProblem(form.password)
    if (problem) return setError(problem)
    if (form.password !== form.confirm) return setError('Les deux mots de passe ne correspondent pas.')

    setBusy(true)
    try {
      await signUp({
        email: form.email.trim(),
        password: form.password,
        last_name: form.last_name.trim(),
        first_name: form.first_name.trim(),
        institution_name: form.institution_name.trim() || undefined,
        subject_taught: form.subject_taught.trim() || undefined,
      })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Inscription impossible.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Créer un compte">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Nom" required value={form.last_name} onChange={set('last_name')} />
          <Field label="Prénom" required value={form.first_name} onChange={set('first_name')} />
        </div>
        <Field label="Adresse email" type="email" required autoComplete="username" value={form.email} onChange={set('email')} />
        <Field label="Mot de passe" type="password" required autoComplete="new-password" hint="8 caractères minimum, dont un chiffre." value={form.password} onChange={set('password')} />
        <Field label="Confirmer le mot de passe" type="password" required autoComplete="new-password" value={form.confirm} onChange={set('confirm')} />
        <Field label="Établissement (facultatif)" value={form.institution_name} onChange={set('institution_name')} />
        <Field label="Matière enseignée (facultatif)" value={form.subject_taught} onChange={set('subject_taught')} />
        {error && <Alert tone="error">{error}</Alert>}
        <Button type="submit" disabled={busy}>
          {busy ? 'Création…' : 'Créer mon compte'}
        </Button>
      </form>
      <p className="mt-6 text-sm text-slate-600">
        Déjà inscrit ?{' '}
        <button type="button" onClick={onGoToLogin} className="font-semibold text-forest underline">
          Se connecter
        </button>
      </p>
    </Card>
  )
}
