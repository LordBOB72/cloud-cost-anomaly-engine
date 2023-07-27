import { useState } from 'react'
import { useBudgets, useCreateBudget, useDeleteBudget } from '../hooks/useCosts'
import clsx from 'clsx'

export function BudgetsPage() {
  const { data: budgets = [], isLoading } = useBudgets()
  const create = useCreateBudget()
  const del    = useDeleteBudget()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '', provider: '', account_id: '',
    tag_key: '', tag_value: '', amount_usd: 1000, period: 'monthly' as const,
  })
  const [err, setErr] = useState<string | null>(null)

  async function submit() {
    setErr(null)
    try {
      await create.mutateAsync({
        ...form,
        provider: form.provider || null,
        account_id: form.account_id || null,
        tag_key: form.tag_key || null,
        tag_value: form.tag_value || null,
      } as Parameters<typeof create.mutateAsync>[0])
      setShowForm(false)
    } catch (e) { setErr(String(e)) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium">Budgets</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="text-sm px-3 py-1.5 bg-blue-500/20 text-blue-400 border border-blue-500/40 rounded hover:bg-blue-500/30 transition-colors">
          + New budget
        </button>
      </div>

      {showForm && (
        <div className="bg-surface-1 border border-surface-3 rounded-lg p-5 space-y-4">
          <h2 className="text-sm font-medium text-gray-400">Create budget</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Name', key: 'name', span: 2 },
              { label: 'Provider (optional)', key: 'provider', placeholder: 'aws | gcp | azure' },
              { label: 'Account ID (optional)', key: 'account_id' },
              { label: 'Tag key (optional)', key: 'tag_key' },
              { label: 'Tag value (optional)', key: 'tag_value' },
            ].map(({ label, key, placeholder, span }) => (
              <div key={key} className={span === 2 ? 'col-span-2' : ''}>
                <label className="block text-xs text-gray-500 mb-1">{label}</label>
                <input value={form[key as keyof typeof form] as string}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  placeholder={placeholder}
                  className="w-full bg-surface-0 border border-surface-3 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500" />
              </div>
            ))}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Amount (USD)</label>
              <input type="number" value={form.amount_usd}
                onChange={(e) => setForm({ ...form, amount_usd: parseFloat(e.target.value) })}
                className="w-full bg-surface-0 border border-surface-3 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Period</label>
              <select value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value as 'monthly' })}
                className="w-full bg-surface-0 border border-surface-3 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
              </select>
            </div>
          </div>
          {err && <p className="text-xs text-red-400 font-mono">{err}</p>}
          <div className="flex justify-end gap-3">
            <button onClick={() => setShowForm(false)} className="text-sm text-gray-500 hover:text-white px-3 py-1.5">Cancel</button>
            <button onClick={submit} disabled={create.isPending || !form.name}
              className="text-sm px-4 py-1.5 bg-blue-500/20 text-blue-400 border border-blue-500/40 rounded hover:bg-blue-500/30 disabled:opacity-50">
              Create
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {isLoading && <p className="text-sm text-gray-500 font-mono animate-pulse">Loading…</p>}
        {budgets.map((b) => (
          <div key={b.id} className="bg-surface-1 border border-surface-3 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-medium text-sm">{b.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {b.period} · {b.provider ? b.provider.toUpperCase() : 'all providers'}
                  {b.account_id ? ` · ${b.account_id}` : ''}
                </p>
              </div>
              <div className="text-right">
                <p className="font-mono text-sm">
                  <span className={clsx(b.burn_pct >= 90 ? 'text-red-400' : b.burn_pct >= 70 ? 'text-yellow-400' : 'text-green-400')}>
                    ${b.current_spend.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                  <span className="text-gray-500"> / ${b.amount_usd.toLocaleString()}</span>
                </p>
                <p className="text-xs text-gray-500">{b.burn_pct.toFixed(1)}% used</p>
              </div>
            </div>
            <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', b.burn_pct >= 90 ? 'bg-red-500' : b.burn_pct >= 70 ? 'bg-yellow-500' : 'bg-green-500')}
                style={{ width: `${Math.min(b.burn_pct, 100)}%` }}
              />
            </div>
            <div className="flex justify-end mt-2">
              <button onClick={() => del.mutate(b.id)} className="text-xs text-gray-600 hover:text-red-400 transition-colors">Delete</button>
            </div>
          </div>
        ))}
        {!isLoading && budgets.length === 0 && (
          <p className="text-sm text-gray-500 font-mono">No budgets defined.</p>
        )}
      </div>
    </div>
  )
}
