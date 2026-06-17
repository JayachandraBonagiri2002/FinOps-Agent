import { useState, useEffect } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { TrendingUp, TrendingDown, Server, IndianRupee, Loader2 } from 'lucide-react'

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/dashboard')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-500" size={32} />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Failed to load dashboard data
      </div>
    )
  }

  const { kpis, daily_trend, by_environment, by_resource, usage_hours, comparison } = data

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-b from-[#0f0f0f] to-[#1a1a1a]">
      <div className="w-full px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Cost Dashboard</h1>
          <p className="text-sm text-gray-500">Real-time Azure cost analysis across all subscriptions</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KpiCard
            title="This Week Spend"
            value={`₹${Math.round(kpis.weekly_spend).toLocaleString()}`}
            subtitle={`${kpis.change_pct > 0 ? '+' : ''}${kpis.change_pct}% vs last week`}
            icon={IndianRupee}
            trend={kpis.change_pct > 0 ? 'up' : 'down'}
          />
          <KpiCard
            title="Monthly Projection"
            value={`₹${Math.round(kpis.monthly_projection).toLocaleString()}`}
            subtitle="Based on current rate"
            icon={TrendingUp}
          />
          <KpiCard
            title="Resources Tracked"
            value={kpis.resources_tracked}
            subtitle="Active resources"
            icon={Server}
          />
          <KpiCard
            title="Potential Savings"
            value={`₹${Math.round(kpis.potential_savings).toLocaleString()}/mo`}
            subtitle="Auto-shutdown + idle cleanup"
            icon={TrendingDown}
            accent="green"
          />
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <ChartCard title="Daily Cost Trend (3 Weeks)">
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={daily_trend}>
                <defs>
                  <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" stroke="#666" tick={{ fill: '#999', fontSize: 11 }}
                  tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="#666" tick={{ fill: '#999', fontSize: 11 }}
                  tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: '#1e1e1e', border: '1px solid #333', borderRadius: 8 }}
                  labelStyle={{ color: '#999' }}
                  formatter={(v) => [`₹${Math.round(v).toLocaleString()}`, 'Cost']}
                />
                <Area type="monotone" dataKey="cost" stroke="#10b981" fill="url(#colorCost)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Cost by Environment">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={by_environment}
                  dataKey="cost"
                  nameKey="environment"
                  cx="50%" cy="50%"
                  outerRadius={100}
                  label={({ environment, percent }) => `${environment} ${(percent*100).toFixed(0)}%`}
                  labelLine={{ stroke: '#666' }}
                >
                  {by_environment.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e1e1e', border: '1px solid #333', borderRadius: 8 }}
                  formatter={(v) => [`₹${Math.round(v).toLocaleString()}`, 'Cost']}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <ChartCard title="Cost by Resource">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={by_resource.slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" stroke="#666" tick={{ fill: '#999', fontSize: 11 }}
                  tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="resource" stroke="#666"
                  tick={{ fill: '#999', fontSize: 11 }} width={140} />
                <Tooltip
                  contentStyle={{ background: '#1e1e1e', border: '1px solid #333', borderRadius: 8 }}
                  formatter={(v) => [`₹${Math.round(v).toLocaleString()}`, 'Cost']}
                />
                <Bar dataKey="cost" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Usage Hours — Dev/Staging (Avg)">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={usage_hours}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="resource" stroke="#666" tick={{ fill: '#999', fontSize: 10 }} />
                <YAxis stroke="#666" tick={{ fill: '#999', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#1e1e1e', border: '1px solid #333', borderRadius: 8 }}
                  formatter={(v) => [`${v.toFixed(1)} hrs`, 'Avg Usage']}
                />
                <Bar dataKey="hours" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Week-over-Week Table */}
        <div className="bg-[#1a1a1a] rounded-2xl border border-[#1a1a1a] overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-[#2a2a2a] bg-[#121212]">
            <h3 className="text-white font-semibold text-sm">Week-over-Week Comparison</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#2a2a2a]">
                  <th className="text-left px-5 py-3 text-gray-400 font-medium">Resource</th>
                  <th className="text-right px-5 py-3 text-gray-400 font-medium">This Week</th>
                  <th className="text-right px-5 py-3 text-gray-400 font-medium">Last Week</th>
                  <th className="text-right px-5 py-3 text-gray-400 font-medium">Change</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row, i) => (
                  <tr key={i} className="border-t border-[#2a2a2a] hover:bg-[#252525]">
                    <td className="px-5 py-3 text-gray-300 font-mono text-xs">{row.resource}</td>
                    <td className="px-5 py-3 text-right text-gray-300">₹{Math.round(row.this_week).toLocaleString()}</td>
                    <td className="px-5 py-3 text-right text-gray-400">₹{Math.round(row.last_week).toLocaleString()}</td>
                    <td className={`px-5 py-3 text-right font-medium ${
                      row.change_pct > 0 ? 'text-red-400' : row.change_pct < 0 ? 'text-green-400' : 'text-gray-500'
                    }`}>
                      {row.change_pct > 0 ? '+' : ''}{row.change_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

function KpiCard({ title, value, subtitle, icon: Icon, trend, accent }) {
  return (
    <div className="bg-gradient-to-br from-[#1a1a1a] to-[#121212] rounded-2xl border border-[#1a1a1a] p-5 shadow-sm hover:border-[#2a2a2a] transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-600 uppercase tracking-widest font-semibold">{title}</span>
        <div className={`p-2 rounded-lg ${accent === 'green' ? 'bg-green-500/15' : 'bg-gray-500/10'}`}>
          <Icon size={16} className={accent === 'green' ? 'text-green-400' : 'text-gray-600'} />
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className={`text-xs mt-2 font-medium ${
        trend === 'up' ? 'text-red-400' : trend === 'down' ? 'text-green-400' : 'text-gray-500'
      }`}>
        {subtitle}
      </div>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-[#1a1a1a] rounded-2xl border border-[#1a1a1a] p-6 shadow-sm hover:border-[#2a2a2a] transition-all">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">{title}</h3>
      {children}
    </div>
  )
}
