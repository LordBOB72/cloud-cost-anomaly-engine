import { useRecommendations, useDismissRecommendation } from '../hooks/useCosts'

const CATEGORY_LABELS: Record<string, string> = {
  idle:               '💤 Idle resource',
  rightsize:          '📐 Right-size',
  reserved_instance:  '📦 Reserved instance',
}

export function RecommendationsPage() {
  const { data: recs = [], isLoading } = useRecommendations()
  const dismiss = useDismissRecommendation()

  const totalSavings = recs.reduce((s, r) => s + (r.savings_usd ?? 0), 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-medium">Recommendations</h1>
          {recs.length > 0 && (
            <p className="text-xs text-gray-500 mt-0.5">
              {recs.length} suggestions · estimated savings ${totalSavings.toLocaleString(undefined, { maximumFractionDigits: 0 })}/mo
            </p>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {isLoading && <p className="text-sm text-gray-500 font-mono animate-pulse">Loading…</p>}
        {recs.map((r) => (
          <div key={r.id} className="bg-surface-1 border border-surface-3 rounded-lg p-4 flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs px-2 py-0.5 rounded bg-surface-3 text-gray-300 font-mono">
                  {CATEGORY_LABELS[r.category] ?? r.category}
                </span>
                <span className="text-xs text-gray-500 uppercase font-mono">{r.provider}</span>
              </div>
              <p className="text-sm text-gray-300">{r.description}</p>
              {r.resource_id && (
                <p className="text-xs text-gray-500 font-mono truncate">{r.resource_id}</p>
              )}
            </div>
            <div className="flex items-center gap-4 shrink-0">
              {r.savings_usd != null && (
                <div className="text-right">
                  <p className="text-sm font-mono text-green-400">
                    ~${r.savings_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}/mo
                  </p>
                  <p className="text-xs text-gray-500">est. savings</p>
                </div>
              )}
              <button
                onClick={() => dismiss.mutate(r.id)}
                className="text-xs text-gray-600 hover:text-gray-400 font-mono transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        ))}
        {!isLoading && recs.length === 0 && (
          <p className="text-sm text-gray-500 font-mono">No recommendations. Run an ingestion first.</p>
        )}
      </div>
    </div>
  )
}
