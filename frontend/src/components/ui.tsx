import { useId, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from 'react'

export function Field({
  label,
  hint,
  ...inputProps
}: { label: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId()
  const hintId = `${id}-hint`
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        {...inputProps}
        id={id}
        aria-describedby={hint ? hintId : undefined}
        className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest disabled:bg-slate-100"
      />
      {hint && (
        <p id={hintId} className="mt-1 text-xs text-slate-500">
          {hint}
        </p>
      )}
    </div>
  )
}

export function Button({
  variant = 'primary',
  ...props
}: { variant?: 'primary' | 'secondary' } & ButtonHTMLAttributes<HTMLButtonElement>) {
  const style =
    variant === 'primary'
      ? 'bg-forest text-white hover:bg-forest-deep'
      : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
  return (
    <button
      {...props}
      className={`rounded-md px-4 py-2 text-sm font-semibold shadow-sm transition disabled:cursor-not-allowed disabled:opacity-50 ${style}`}
    />
  )
}

export function Alert({
  tone,
  children,
}: {
  tone: 'error' | 'success' | 'info'
  children: ReactNode
}) {
  const style = {
    error: 'border-laterite bg-orange-50 text-laterite',
    success: 'border-forest bg-green-50 text-forest-deep',
    info: 'border-gold bg-amber-50 text-slate-700',
  }[tone]
  return (
    <p role={tone === 'error' ? 'alert' : 'status'} className={`rounded-md border px-3 py-2 text-sm ${style}`}>
      {children}
    </p>
  )
}

export function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mx-auto w-full max-w-md rounded-xl bg-white p-8 shadow-md">
      <p className="text-xs font-semibold tracking-widest text-gold">NKULIA</p>
      <h1 className="mt-1 mb-6 text-2xl font-bold text-forest-deep">{title}</h1>
      {children}
    </section>
  )
}
