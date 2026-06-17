import { useState, useEffect, useCallback, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  TrendingUp, IndianRupee, Server,
  PiggyBank, RefreshCw, AlertCircle, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import clsx from 'clsx'

// --- Utilities ---
function fmt(val) {
  if (val == null || isNaN(val)) return '₹0'
  if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`
  return `₹${Math.round(val)}`
}

function fmtDate(str) {
  if (!str) return ''
  const d = new Date(str)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

// --- ECharts Dark Theme ---
const ECHARTS_THEME = {
  backgroundColor: 'transparent',
  textStyle: { color: '#a1a1aa', fontFamily: "'Inter', sans-serif" },
  title: { textStyle: { color: '#f4f4f5' } },
}

const COLORS = ['#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#38bdf8', '#4ade80', '#fb923c']

// --- KPI Card ---
function KPICard({ title, value, change, icon: Icon, accent, subtitle }) {
  const up = change > 0
  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-4 flex flex-col justify-between min-h-[120px] hover:border-border transition-colors group">
      <div className="flex items-center justify-between">
        <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105", accent)}>
          <Icon size={19} />
        </div>
        {change != null && change !== 0 && (
          <span className={clsx(
            "flex items-center gap-0.5 text-[11px] font-semibold px-2 py-0.5 rounded-md",
            up ? "bg-danger/10 text-danger" : "bg-success/10 text-success"
          )}>
            {up ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-text-primary tracking-tight leading-none">{value}</p>
        <p className="text-[11px] text-text-muted mt-1.5">{title}</p>
        {subtitle && <p className="text-[10px] text-text-muted/70 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

// --- Chart Panel Wrapper ---
function ChartPanel({ title, children, className }) {
  return (
    <div className={clsx("bg-surface-1 border border-border-subtle rounded-xl p-5", className)}>
      <h3 className="text-xs font-semibold text-text-primary mb-1 tracking-wide uppercase opacity-70">{title}</h3>
      {children}
    </div>
  )
}

// --- Loading Skeleton ---
function Skeleton() {
  return (
    <div className="p-5 space-y-5">
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-surface-1 border border-border-subtle rounded-xl p-4 h-[120px]">
            <div className="w-10 h-10 rounded-lg animate-shimmer mb-3" />
            <div className="h-7 w-24 rounded animate-shimmer mb-1" />
            <div className="h-3 w-16 rounded animate-shimmer" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 bg-surface-1 border border-border-subtle rounded-xl p-5 h-80">
          <div className="h-4 w-40 rounded animate-shimmer mb-4" />
          <div className="h-60 w-full rounded-lg animate-shimmer" />
        </div>
        <div className="bg-surface-1 border border-border-subtle rounded-xl p-5 h-80">
          <div className="h-4 w-28 rounded animate-shimmer mb-4" />
          <div className="h-60 w-full rounded-lg animate-shimmer" />
        </div>
      </div>
    </div>
  )
}

// --- Main Dashboard ---
export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/dashboard')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // --- Chart Options (memoized) ---
  const trendOption = useMemo(() => {
    if (!data?.daily_trend?.length) return null
    const dates = data.daily_trend.map(d => fmtDate(d.date))
    const costs = data.daily_trend.map(d => d.cost)
    return {
      ...ECHARTS_THEME,
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1c1c1f',
        borderColor: '#3f3f46',
        textStyle: { color: '#f4f4f5', fontSize: 12 },
        formatter: (params) => {
          const p = params[0]
          return `<div style="font-size:11px;color:#71717a">${p.name}</div><div style="font-size:14px;font-weight:600;color:#f4f4f5;margin-top:2px">${fmt(p.value)}</div>`
        },
      },
      grid: { top: 20, right: 16, bottom: 28, left: 50 },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#27272a' } },
        axisTick: { show: false },
        axisLabel: { color: '#71717a', fontSize: 10, interval: 'auto' },
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#27272a', type: 'dashed' } },
        axisLabel: { color: '#71717a', fontSize: 10, formatter: (v) => fmt(v) },
      },
      series: [{
        type: 'line',
        data: costs,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        showSymbol: false,
        lineStyle: { width: 2.5, color: '#60a5fa' },
        itemStyle: { color: '#60a5fa' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(96,165,250,0.3)' },
              { offset: 1, color: 'rgba(96,165,250,0.02)' },
            ],
          },
        },
        emphasis: { itemStyle: { borderWidth: 2, borderColor: '#fff' } },
      }],
      animationDuration: 1000,
      animationEasing: 'cubicOut',
    }
  }, [data?.daily_trend])

  const pieOption = useMemo(() => {
    if (!data?.by_environment?.length) return null
    return {
      ...ECHARTS_THEME,
      tooltip: {
        trigger: 'item',
        backgroundColor: '#1c1c1f',
        borderColor: '#3f3f46',
        textStyle: { color: '#f4f4f5', fontSize: 12 },
        formatter: (p) => `<div style="font-size:11px;color:#71717a">${p.name}</div><div style="font-size:14px;font-weight:600;color:#f4f4f5;margin-top:2px">${fmt(p.value)} <span style="color:#71717a;font-size:11px">(${p.percent}%)</span></div>`,
      },
      legend: {
        orient: 'vertical',
        right: 8,
        top: 'center',
        itemWidth: 8,
        itemHeight: 8,
        itemGap: 10,
        textStyle: { color: '#a1a1aa', fontSize: 10 },
        formatter: (name) => name.length > 14 ? name.slice(0, 14) + '…' : name,
      },
      series: [{
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderColor: '#121214', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 20, shadowColor: 'rgba(96,165,250,0.3)' },
          label: { show: true, fontSize: 12, fontWeight: 600, color: '#f4f4f5' },
        },
        data: data.by_environment.map((item, i) => ({
          name: item.environment,
          value: item.cost,
          itemStyle: { color: COLORS[i % COLORS.length] },
        })),
      }],
      animationDuration: 800,
      animationEasing: 'cubicOut',
    }
  }, [data?.by_environment])

  const barOption = useMemo(() => {
    if (!data?.by_resource?.length) return null
    const resources = data.by_resource.slice(0, 10).reverse()
    return {
      ...ECHARTS_THEME,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#1c1c1f',
        borderColor: '#3f3f46',
        textStyle: { color: '#f4f4f5', fontSize: 12 },
        formatter: (params) => {
          const p = params[0]
          return `<div style="font-size:11px;color:#71717a">${p.name}</div><div style="font-size:14px;font-weight:600;color:#f4f4f5;margin-top:2px">${fmt(p.value)}</div>`
        },
      },
      grid: { top: 8, right: 16, bottom: 8, left: 110 },
      xAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#27272a', type: 'dashed' } },
        axisLabel: { color: '#71717a', fontSize: 10, formatter: (v) => fmt(v) },
      },
      yAxis: {
        type: 'category',
        data: resources.map(r => r.resource),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#a1a1aa', fontSize: 10, width: 100, overflow: 'truncate',
          formatter: (v) => v.length > 16 ? v.slice(0, 16) + '…' : v,
        },
      },
      series: [{
        type: 'bar',
        data: resources.map((r, i) => ({
          value: r.cost,
          itemStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: 'rgba(96,165,250,0.8)' },
                { offset: 1, color: 'rgba(96,165,250,0.3)' },
              ],
            },
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barWidth: 16,
        emphasis: { itemStyle: { color: '#60a5fa' } },
      }],
      animationDuration: 800,
      animationEasing: 'cubicOut',
    }
  }, [data?.by_resource])

  const gaugeOption = useMemo(() => {
    if (!data?.kpis) return null
    const savings = data.kpis.potential_savings || 0
    const monthly = data.kpis.monthly_projection || 1
    const pct = Math.min((savings / monthly) * 100, 100)
    return {
      ...ECHARTS_THEME,
      series: [{
        type: 'gauge',
        startAngle: 220,
        endAngle: -40,
        min: 0,
        max: 100,
        radius: '90%',
        progress: { show: true, width: 14, roundCap: true, itemStyle: { color: '#34d399' } },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 14, color: [[1, '#27272a']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: true, offsetCenter: [0, '70%'], fontSize: 11, color: '#71717a' },
        detail: {
          valueAnimation: true, offsetCenter: [0, '10%'],
          fontSize: 22, fontWeight: 700, color: '#34d399',
          formatter: (v) => `${v.toFixed(0)}%`,
        },
        data: [{ value: pct, name: 'Savings Potential' }],
      }],
      animationDuration: 1200,
      animationEasing: 'cubicOut',
    }
  }, [data?.kpis])

  // --- Render ---
  if (loading) return <Skeleton />

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center">
          <AlertCircle size={36} className="text-danger mx-auto mb-3" />
          <p className="text-sm text-text-secondary mb-2">Failed to load dashboard</p>
          <p className="text-xs text-text-muted mb-4">{error}</p>
          <button onClick={() => fetchData()} className="px-4 py-2 rounded-lg bg-accent text-white text-sm hover:bg-accent-muted transition">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const { kpis, comparison } = data

  return (
    <div className="p-4 sm:p-5 lg:p-6 xl:p-8 space-y-5 w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary tracking-tight">Cost Dashboard</h1>
          <p className="text-[11px] text-text-muted mt-0.5">Real-time Azure cost analytics &bull; Auto-refreshes</p>
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-text-secondary hover:bg-surface-2 hover:text-text-primary transition disabled:opacity-50"
        >
          <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 xl:gap-4">
        <KPICard title="Weekly Spend" value={fmt(kpis?.weekly_spend)} change={kpis?.change_pct} icon={IndianRupee} accent="bg-accent/15 text-accent" subtitle="Last 7 days" />
        <KPICard title="Monthly Projection" value={fmt(kpis?.monthly_projection)} icon={TrendingUp} accent="bg-[#a78bfa]/15 text-[#a78bfa]" subtitle="Based on current rate" />
        <KPICard title="Resources Tracked" value={kpis?.resources_tracked || 0} icon={Server} accent="bg-success/15 text-success" subtitle="Active resources" />
        <KPICard title="Potential Savings" value={fmt(kpis?.potential_savings)} icon={PiggyBank} accent="bg-warning/15 text-warning" subtitle="Monthly estimate" />
      </div>

      {/* Row 1: Area Trend + Donut */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <ChartPanel title="Daily Cost Trend" className="xl:col-span-2">
          {trendOption ? (
            <ReactECharts option={trendOption} style={{ height: 280 }} opts={{ renderer: 'canvas' }} />
          ) : (
            <div className="h-[280px] flex items-center justify-center text-text-muted text-xs">No trend data</div>
          )}
        </ChartPanel>

        <ChartPanel title="Cost Distribution">
          {pieOption ? (
            <ReactECharts option={pieOption} style={{ height: 280 }} opts={{ renderer: 'canvas' }} />
          ) : (
            <div className="h-[280px] flex items-center justify-center text-text-muted text-xs">No data</div>
          )}
        </ChartPanel>
      </div>

      {/* Row 2: Bar + Gauge + Comparison Table */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* Horizontal bar chart */}
        <ChartPanel title="Top Resources by Cost" className="xl:col-span-5">
          {barOption ? (
            <ReactECharts option={barOption} style={{ height: 320 }} opts={{ renderer: 'canvas' }} />
          ) : (
            <div className="h-[320px] flex items-center justify-center text-text-muted text-xs">No data</div>
          )}
        </ChartPanel>

        {/* Gauge */}
        <ChartPanel title="Savings Potential" className="xl:col-span-3">
          {gaugeOption ? (
            <ReactECharts option={gaugeOption} style={{ height: 220 }} opts={{ renderer: 'canvas' }} />
          ) : (
            <div className="h-[220px] flex items-center justify-center text-text-muted text-xs">No data</div>
          )}
          <div className="text-center mt-2">
            <p className="text-xs text-text-muted">
              {fmt(kpis?.potential_savings || 0)}/mo saveable
            </p>
            <p className="text-[10px] text-text-muted/60 mt-0.5">
              of {fmt(kpis?.monthly_projection || 0)} projected
            </p>
          </div>
        </ChartPanel>

        {/* Comparison table */}
        <ChartPanel title="Week-over-Week" className="xl:col-span-4">
          <div className="h-[320px] overflow-y-auto">
            {comparison?.length > 0 ? (
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-surface-1 z-10">
                  <tr className="border-b border-border">
                    <th className="text-left text-text-muted font-medium py-2 pr-2">Resource</th>
                    <th className="text-right text-text-muted font-medium py-2 px-1">Current</th>
                    <th className="text-right text-text-muted font-medium py-2 pl-1 w-14">Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.slice(0, 15).map((row, i) => {
                    const ch = row.change_pct || 0
                    return (
                      <tr key={i} className="border-b border-border-subtle/40 hover:bg-surface-2/30 transition-colors">
                        <td className="py-1.5 pr-2 text-text-secondary truncate max-w-[100px]">{row.resource}</td>
                        <td className="py-1.5 px-1 text-right text-text-primary font-medium">{fmt(row.this_week || 0)}</td>
                        <td className="py-1.5 pl-1 text-right">
                          <span className={clsx(
                            "font-semibold text-[11px]",
                            ch > 5 ? "text-danger" : ch < -5 ? "text-success" : "text-text-muted"
                          )}>
                            {ch > 0 ? '+' : ''}{ch.toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : (
              <div className="h-full flex items-center justify-center text-text-muted text-xs">No comparison data</div>
            )}
          </div>
        </ChartPanel>
      </div>
    </div>
  )
}
