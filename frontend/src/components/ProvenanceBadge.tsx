/**
 * Les quatre étiquettes de provenance (docs/ARCHITECTURE.md, principe
 * non négociable n°2). Même vocabulaire et mêmes codes que le contrat
 * de génération du backend.
 */
export type Provenance = 'reference' | 'deduction' | 'ai_recommendation' | 'missing_information'

const STYLES: Record<Provenance, { label: string; className: string }> = {
  reference: { label: 'Référence', className: 'bg-green-100 text-forest-deep' },
  deduction: { label: 'Déduction', className: 'bg-sky-100 text-sky-900' },
  ai_recommendation: { label: 'Recommandation IA', className: 'bg-amber-100 text-amber-900' },
  missing_information: { label: 'Information manquante', className: 'bg-slate-200 text-slate-700' },
}

export function ProvenanceBadge({ provenance }: { provenance: Provenance }) {
  const { label, className } = STYLES[provenance]
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${className}`}>
      {label}
    </span>
  )
}
