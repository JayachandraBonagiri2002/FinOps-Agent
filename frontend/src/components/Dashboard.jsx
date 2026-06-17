import { useState, useEffect } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { TrendingUp, TrendingDown, Server, IndianRupee, Loader2, RefreshCw } from 'lucide-react'

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchData = () => {
    setLoading(true)
    setError(false)
    fetch('/api/dashboard')
      .then(r => r.json())
      .then(d => { setData(d); setError(false) })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-gray-500" size={32} />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px] gap-4">
        <p className="text-gray-400 text-sm">Unable to load dashboard</p>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-300 bg-[#151515] border border-[#2a2a2a] rounded-lg hover:border-[#3a3a3a] transition-colors"
        >
          <RefreshCw size={14} />
          Retry
        </button>
      </div>
    )
  }

  const { kpis, daily_trend, by_environment, by_resource, usage_hours, comparison } = data

  const emptyKpis = !kpis
  const safeKpis = kpis || { weekly_spend: 0, change_pct: 0, monthly_projection: 0, resources_tracked: 0, potential_savings: 0 }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="w-full p-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiCard
            title="This Week Spend"
            value={`₹${Math.round(safeKpis.weekly_spend).toLocaleString('en-IN')}`}
            subtitle={emptyKpis ? 'No data' : `${safeKpis.change_pct > 0 ? '+' : ''}${safeKpis.change_pct}% vs last week`}
            icon={IndianRupee}
            trend={emptyKpis ? null : safeKpis.change_pct > 0 ? 'up' : 'down'}
          />
          <KpiCard
            title="Monthly Projection"
            value={`₹${Math.round(safeKpis.monthly_projection).toLocaleString('en-IN')}`}
            subtitle={emptyKpis ? 'No data' : 'Based on current rate'}
            icon={TrendingUp}
          />
          <KpiCard
            title="Resources Tracked"
            value={safeKpis.resources_tracked}
            subtitle={emptyKpis ? 'No data' : 'Active resources'}
            icon={Server}
          />
          <KpiCard
            title="Potential Savings"
            value={`₹${Math.round(safeKpis.potential_savings).toLocaleString('en-IN')}/mo`}
            subtitle={emptyKpis ? 'No data' : 'Auto-shutdown + idle cleanup'}
            icon={TrendingDown}
            accent="green"
          />
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard title="Daily Cost Trend (3 Weeks)">
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={daily_trend || []}>
                <defs>
                  <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="date" stroke="#333" tick={{ fill: '#666', fontSize: 11 }}
                  tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="#333" tick={{ fill: '#666', fontSize: 11 }}
                  tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 8 }}
                  labelStyle={{ color: '#888' }}
                  formatter={(v) => [`₹${Math.round(v).toLocaleString('en-IN')}`, 'Cost']}
                />
                <Area type="monotone" dataKey="cost" stroke="#10b981" fill="url(#colorCost)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Cost by Environment">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={by_environment || []}
                  dataKey="cost"
                  nameKey="environment"
                  cx="50%" cy="50%"
                  outerRadius={100}
                  label={({ environment, percent }) => `${environment} ${(percent*100).toFixed(0)}%`}
                  labelLine={{ stroke: '#444' }}
                >
                  {(by_environment || []).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 8 }}
                  formatter={(v) => [`₹${Math.round(v).toLocaleString('en-IN')}`, 'Cost']}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard title="Cost by Resource">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={(by_resource || []).slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis type="number" stroke="#333" tick={{ fill: '#666', fontSize: 11 }}
                  tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="resource" stroke="#333"
                  tick={{ fill: '#666', fontSize: 11 }} width={140} />
                <Tooltip
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 8 }}
                  formatter={(v) => [`₹${Math.round(v).toLocaleString('en-IN')}`, 'Cost']}
                />
                <Bar dataKey="cost" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Usage Hours — Dev/Staging (Avg)">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={usage_hours || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="resource" stroke="#333" tick={{ fill: '#666', fontSize: 10 }} />
                <YAxis stroke="#333" tick={{ fill: '#666', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 8 }}
                  formatter={(v) => [`${v.toFixed(1)} hrs`, 'Avg Usage']}
                />
                <Bar dataKey="hours" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Week-over-Week Table */}
        <div className="bg-[#151515] rounded-xl border border-[#2a2a2a] overflow-hidden">
          <div className="px-5 py-3 border-b border-[#2a2a2a]">
            <h3 className="text-white font-semibold text-sm">Week-over-Week Comparison</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#1a1a1a]">
                  <th className="text-left px-5 py-3 text-gray-500 font-medium text-xs uppercase tracking-wide">Resource</th>
                  <th className="text-right px-5 py-3 text-gray-500 font-medium text-xs uppercase tracking-wide">This Week</th>
                  <th className="text-right px-5 py-3 text-gray-500 font-medium text-xs uppercase tracking-wide">Last Week</th>
                  <th className="text-right px-5 py-3 text-gray-500 font-medium text-xs uppercase tracking-wide">Change</th>
                </tr>
              </thead>
              <tbody>
                {(comparison || []).map((row, i) => (
                  <tr
                    key={i}
                    className={`border-t border-[#222] hover:bg-[#1a1a1a] transition-colors ${
                      i % 2 === 0 ? 'bg-[#151515]' : 'bg-[#111]'
                    }`}
                  >
                    <td className="px-5 py-3 text-gray-300 font-mono text-xs">{row.resource}</td>
                    <td className="px-5 py-3 text-right text-gray-300">₹{Math.round(row.this_week).toLocaleString('en-IN')}</td>
                    <td className="px-5 py-3 text-right text-gray-400">₹{Math.round(row.last_week).toLocaleString('en-IN')}</td>
                    <td className={`px-5 py-3 text-right font-medium ${
                      row.change_pct > 0 ? 'text-red-400' : row.change_pct < 0 ? 'text-emerald-400' : 'text-gray-500'
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
    <div className="bg-[#151515] rounded-xl border border-[#2a2a2a] p-5 hover:border-[#3a3a3a] transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">{title}</span>
        <div className={`p-2 rounded-lg ${accent === 'green' ? 'bg-emerald-500/10' : 'bg-white/5'}`}>
          <Icon size={16} className={accent === 'green' ? 'text-emerald-400' : 'text-gray-400'} />
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className={`text-xs mt-2 font-medium ${
        trend === 'up' ? 'text-red-400' : trend === 'down' ? 'text-emerald-400' : 'text-gray-500'
      }`}>
        {subtitle}
      </div>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-[#151515] rounded-xl border border-[#2a2a2a] p-5 hover:border-[#3a3a3a] transition-colors">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">{title}</h3>
      {children}
    </div>
  )
}
