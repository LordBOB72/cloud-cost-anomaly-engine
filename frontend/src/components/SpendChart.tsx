import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import type { DailyCostRow } from '../types'
import { format, parseISO } from 'date-fns'

interface Props {
  data: DailyCostRow[]
}

const PROVIDER_COLORS: Record<string, string> = {
  aws:   '#f97316',
  gcp:   '#3b82f6',
  azure: '#8b5cf6',
}

export function SpendChart({ data }: Props) {
  // pivot: date -> { aws, gcp, azure }
  const byDate = new Map<string, Record<string, number>>()
  for (const row of data) {
    const label = format(parseISO(row.usage_date), 'MMM d')
    if (!byDate.has(label)) byDate.set(label, {})
    byDate.get(label)![row.provider] = (byDate.get(label)![row.provider] ?? 0) + row.total_cost
  }
  const chartData = Array.from(byDate.entries()).map(([label, vals]) => ({ label, ...vals }))

  const providers = [...new Set(data.map((r) => r.provider))]

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
        <defs>
          {providers.map((p) => (
            <linearGradient key={p} id={`grad-${p}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={PROVIDER_COLORS[p]} stopOpacity={0.35} />
              <stop offset="95%" stopColor={PROVIDER_COLORS[p]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1c2a40" />
        <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
          tickFormatter={(v) => `$${v.toLocaleString()}`} />
        <Tooltip
          contentStyle={{ background: '#0f1623', border: '1px solid #1c2a40', borderRadius: 6, fontSize: 12 }}
          formatter={(val: number) => `$${val.toFixed(2)}`}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: '#64748b' }} />
        {providers.map((p) => (
          <Area key={p} type="monotone" dataKey={p} stroke={PROVIDER_COLORS[p]}
            fill={`url(#grad-${p})`} strokeWidth={1.5} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}
