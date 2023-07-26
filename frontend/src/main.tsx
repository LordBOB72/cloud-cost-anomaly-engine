import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { DashboardPage } from './pages/DashboardPage'
import { AnomaliesPage } from './pages/AnomaliesPage'
import { BudgetsPage } from './pages/BudgetsPage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import './index.css'

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 2 } } })

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-0 font-sans text-gray-200">
        <header className="border-b border-surface-3 bg-surface-1 px-6 py-3 flex items-center gap-6">
          <span className="font-mono text-cyan-400 text-sm font-medium">💰 cost-anomaly-engine</span>
          <nav className="flex gap-1 ml-4">
            {[
              { to: '/', label: 'Dashboard' },
              { to: '/anomalies', label: 'Anomalies' },
              { to: '/budgets', label: 'Budgets' },
              { to: '/recommendations', label: 'Recommendations' },
            ].map(({ to, label }) => (
              <NavLink key={to} to={to} end={to === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded text-sm transition-colors ${isActive ? 'bg-surface-3 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-2'}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="p-6 max-w-6xl mx-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/anomalies" element={<AnomaliesPage />} />
            <Route path="/budgets" element={<BudgetsPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}><App /></QueryClientProvider>
  </React.StrictMode>
)
