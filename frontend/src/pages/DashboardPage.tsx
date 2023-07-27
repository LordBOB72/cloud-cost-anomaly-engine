import { useDailyCosts, useCostSummary, useAnomalies, useTriggerIngestion } from '../hooks/useCosts'
import { SpendChart } from '../components/SpendChart'
import { formatDistanceToNow } from 'date-fns'

export function DashboardPage() {
  const { data: daily = [] }    = useDailyCosts()
  const { data: summary = [] }  = useCostSummary()
  const { data: anomalies = [] } = useAnomalies()
  const trigger = useTriggerIngestion()

  const totalSpend = summary.reduce((s, r) => s + r.total_cost, 0)
  const openAnomalies = anomalies.filter((a) => !a.resolved).length
  const highConfidence = anomalies.filter((a) => !a.resolved && a.confidence >= 80).length

  const topServices = [...summary]
    .sort((a, b) => b.total_cost - a.total_cost)
    .slice(0, 8)

  return (
    <div className="space-y-6">
      {/* stat cards */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Total spend (30d)" value={`$${totalSpend.toLocaleString(undefined, { maximumFractionDigits: 2 })}`} />
        <StatCard label="Open anomalies" value={String(openAnomalies)} highlight={openAnomalies > 0} />
        <StatCard label="High-confidence alerts" value={String(highConfidence)} highlight={highConfidence > 0} />
      </div>

      {/* spend chart */}
      <div className="bg-surface-1 border border-surface-3 rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-gray-300">Daily spend — last 30 days</h2>
          <button
            onClick={() => trigger.mutate(1)}
            disabled={trigger.isPending}
            className="text-xs px-3 py-1.5 bg-surface-3 border border-surface-3 hover:border-blue-500 text-gray-400 rounded font-mono transition-colors disabled:opacity-50"
          >
            {trigger.isPending ? 'ingesting…' : '⟳ ingest now'}
          </button>
        </div>
        <SpendChart data={daily} />
      </div>

      {/* top services */}
      <div className="bg-surface-1 border border-surface-3 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-300 mb-4">Top services by spend</h2>
        <div className="space-y-2">
          {topServices.map((row, i) => {
            const pct = totalSpend > 0 ? (row.total_cost / totalSpend) * 100 : 0
            return (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs font-mono text-gray-500 w-8 text-right">{i + 1}</span>
                <span className="text-xs font-mono text-cyan-400 w-32 truncate">{row.provider.toUpperCase()}</span>
                <span className="text-xs text-gray-300 flex-1 truncate">{row.service}</span>
                <div className="w-32 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs font-mono text-gray-300 w-24 text-right">
                  ${row.total_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </span>
              </div>
            )
          })}
          {topServices.length === 0 && (
            <p className="text-sm text-gray-500 font-mono">No cost data yet. Trigger an ingestion above.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`bg-surface-1 border rounded-lg p-4 ${highlight ? 'border-red-500/40' : 'border-surface-3'}`}>
      <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-mono font-medium ${highlight ? 'text-red-400' : 'text-white'}`}>{value}</p>
    </div>
  )
}
