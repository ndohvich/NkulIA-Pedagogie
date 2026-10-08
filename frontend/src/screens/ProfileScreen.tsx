import { useState, type FormEvent } from 'react'
import { Alert, Button, Field } from '../components/ui'
import { useAuth } from '../auth/AuthContext'
import type { ProfileUpdate } from '../api/auth'

export function ProfileScreen() {
  const { teacher, saveProfile } = useAuth()
  const [form, setForm] = useState({
    last_name: teacher?.last_name ?? '',
    first_name: teacher?.first_name ?? '',
    institution_name: teacher?.institution_name ?? '',
    subject_taught: teacher?.subject_taught ?? '',
    specialty: teacher?.specialty ?? '',
    grade: teacher?.grade ?? '',
    function: teacher?.function ?? '',
  })
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const [busy, setBusy] = useState(false)

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((previous) => ({ ...previous, [key]: e.target.value }))

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setMessage(null)
    setBusy(true)
    const update: ProfileUpdate = {
      last_name: form.last_name.trim(),
      first_name: form.first_name.trim(),
      institution_name: form.institution_name.trim(),
      subject_taught: form.subject_taught.trim() || null,
      specialty: form.specialty.trim() || null,
      grade: form.grade.trim() || null,
      function: form.function.trim() || null,
    }
    try {
      await saveProfile(update)
      setMessage({ tone: 'success', text: 'Profil enregistré.' })
    } catch (caught) {
      setMessage({
        tone: 'error',
        text: caught instanceof Error ? caught.message : "L'enregistrement a échoué.",
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto w-full max-w-2xl rounded-xl bg-white p-8 shadow-md">
      <h1 className="text-2xl font-bold text-forest-deep">Mon profil</h1>
      <p className="mt-1 mb-6 text-sm text-slate-600">
        Ces informations figurent dans l'en-tête de vos documents exportés. Adresse :{' '}
        <strong>{teacher?.email}</strong>
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Nom" required value={form.last_name} onChange={set('last_name')} />
          <Field label="Prénom" required value={form.first_name} onChange={set('first_name')} />
          <Field label="Établissement" value={form.institution_name} onChange={set('institution_name')} />
          <Field label="Matière enseignée" value={form.subject_taught} onChange={set('subject_taught')} />
          <Field label="Spécialité" value={form.specialty} onChange={set('specialty')} />
          <Field label="Grade" value={form.grade} onChange={set('grade')} />
          <Field label="Fonction" value={form.function} onChange={set('function')} />
        </div>
        {message && <Alert tone={message.tone}>{message.text}</Alert>}
        <Button type="submit" disabled={busy}>
          {busy ? 'Enregistrement…' : 'Enregistrer'}
        </Button>
      </form>
    </section>
  )
}
