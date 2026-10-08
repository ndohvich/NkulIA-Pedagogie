/** Même règle que le backend (backend/app/schemas/teacher.py) : 8 caractères, un chiffre. */
export function passwordProblem(password: string): string | null {
  if (password.length < 8) return 'Le mot de passe doit contenir au moins 8 caractères.'
  if (!/\d/.test(password)) return 'Le mot de passe doit contenir au moins un chiffre.'
  return null
}
