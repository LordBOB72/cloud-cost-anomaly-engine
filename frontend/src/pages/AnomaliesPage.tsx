import { useAnomalies, useResolveAnomaly } from '../hooks/useCosts'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export function AnomaliesPage() {
  const { data: anomalies = [], isLoading } = useAnomalies()
  const resolve = useResolveAnomaly()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium">Anomalies</h1>
        <a
          href="/api/v1/export/anomalies.csv"
          className="text-xs px-3 py-1.5 bg-surface-2 border border-surface-3 text-gray-400 rounded hover:text-white transition-colors font-mono"
        >
          ↓ Export CSV
        </a>
      </div>

      <div className="rounded-lg border border-surface-3 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-2 border-b border-surface-3 text-left">
              <th className="px-4 py-3 text-gray-400 font-medium">Provider</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Service</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Region</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Date</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Actual</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Expected</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Confidence</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500 font-mono text-sm animate-pulse">Loading…</td></tr>
            )}
            {anomalies.map((a) => (
              <tr key={a.id} className={clsx('border-b border-surface-3 last:border-0', a.resolved && 'opacity-40')}>
                <td className="px-4 py-3 font-mono text-xs uppercase text-cyan-400">{a.provider}</td>
                <td className="px-4 py-3 text-gray-300 text-xs max-w-[180px] truncate">{a.service}</td>
                <td className="px-4 py-3 text-gray-500 text-xs font-mono">{a.region || '—'}</td>
                <td className="px-4 py-3 text-gray-400 text-xs font-mono">{a.usage_date}</td>
                <td className="px-4 py-3 font-mono text-xs text-red-400">
                  ${a.actual_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">
                  ${a.expected_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3">
                  <ConfidenceBadge value={a.confidence} />
                </td>
                <td className="px-4 py-3">
                  {!a.resolved && (
                    <button
                      onClick={() => resolve.mutate(a.id)}
                      className="text-xs text-gray-500 hover:text-green-400 font-mono transition-colors"
                    >
                      Resolve
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!isLoading && anomalies.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-10 text-center text-gray-500 font-mono text-sm">✓ No anomalies detected</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ConfidenceBadge({ value }: { value: number }) {
  const color = value >= 80 ? 'text-red-400 border-red-500/40 bg-red-500/10'
    : value >= 50 ? 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10'
    : 'text-gray-400 border-gray-500/40 bg-gray-500/10'
  return (
    <span className={`text-xs font-mono px-2 py-0.5 rounded border ${color}`}>
      {value.toFixed(0)}%
    </span>
  )
}
