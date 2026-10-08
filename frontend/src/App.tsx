import { useState } from 'react'
import { AuthProvider } from './auth/AuthProvider'
import { useAuth } from './auth/AuthContext'
import { Button } from './components/ui'
import { ImportScreen } from './screens/ImportScreen'
import { LoginScreen } from './screens/LoginScreen'
import { ProfileScreen } from './screens/ProfileScreen'
import { RegisterScreen } from './screens/RegisterScreen'

function Shell() {
  const { status, teacher, signOut } = useAuth()
  const [anonymousView, setAnonymousView] = useState<'login' | 'register'>('login')
  const [tab, setTab] = useState<'import' | 'profile'>('import')

  if (status === 'loading') {
    return (
      <main className="grid min-h-screen place-items-center bg-stone-50 text-slate-600">
        <p>Chargement…</p>
      </main>
    )
  }

  if (status === 'anonymous') {
    return (
      <main className="grid min-h-screen place-items-center bg-stone-50 px-4 py-10">
        {anonymousView === 'login' ? (
          <LoginScreen onGoToRegister={() => setAnonymousView('register')} />
        ) : (
          <RegisterScreen onGoToLogin={() => setAnonymousView('login')} />
        )}
      </main>
    )
  }

  return (
    <div className="min-h-screen bg-stone-50 text-slate-800">
      <header className="flex items-center justify-between bg-forest-deep px-8 py-4 text-white">
        <div className="flex items-center gap-8">
          <p className="text-lg font-bold tracking-wide">
            Nkul<span className="text-gold">IA</span>
          </p>
          <nav aria-label="Navigation principale" className="flex gap-4 text-sm">
            {(
              [
                ['import', 'Import'],
                ['profile', 'Profil'],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                aria-current={tab === id ? 'page' : undefined}
                onClick={() => setTab(id)}
                className={`pb-1 ${tab === id ? 'border-b-2 border-gold font-semibold' : 'opacity-80 hover:opacity-100'}`}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span>
            {teacher?.first_name} {teacher?.last_name}
          </span>
          <Button variant="secondary" onClick={() => void signOut()}>
            Se déconnecter
          </Button>
        </div>
      </header>
      <main className="px-4 py-10">
        {tab === 'import' ? <ImportScreen /> : <ProfileScreen />}
      </main>
    </div>
  )
}

export function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  )
}
