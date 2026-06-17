import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  MessageSquare, LayoutDashboard, ShieldCheck,
  PanelLeftClose, PanelLeft, Plus, Zap, Activity,
  CircleDot
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'approvals', label: 'Approvals', icon: ShieldCheck },
]

export default function Sidebar({ activeView, setActiveView, isOpen, onToggle, onNewChat }) {
  const [status, setStatus] = useState({ live_mode: false, tool_calls_count: 0, pending_approvals: 0 })

  useEffect(() => {
    const fetchStatus = () => {
      fetch('/api/status')
        .then(r => r.ok ? r.json() : null)
        .then(d => d && setStatus(d))
        .catch(() => {})
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 8000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div
      style={{
        width: isOpen ? 220 : 56,
        minWidth: isOpen ? 220 : 56,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #27272a',
        background: '#09090b',
        transition: 'width 0.2s ease, min-width 0.2s ease',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div style={{ height: 48, display: 'flex', alignItems: 'center', padding: '0 12px', gap: 8, borderBottom: '1px solid #27272a', flexShrink: 0 }}>
        {isOpen && (
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="w-6 h-6 rounded-md bg-accent/20 flex items-center justify-center shrink-0">
              <Zap size={12} className="text-accent" />
            </div>
            <span className="text-xs font-semibold truncate text-text-primary">FinOps Copilot</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-md hover:bg-surface-3 text-text-muted hover:text-text-primary transition-colors shrink-0"
        >
          {isOpen ? <PanelLeftClose size={16} /> : <PanelLeft size={16} />}
        </button>
      </div>

      {/* New Chat */}
      <div style={{ padding: '8px 8px 4px' }}>
        <button
          onClick={onNewChat}
          className={clsx(
            "w-full flex items-center gap-2 rounded-lg border border-border text-xs transition-all",
            "hover:bg-surface-3 hover:border-accent/30 active:scale-[0.97]",
            isOpen ? "px-2.5 py-2" : "justify-center py-2"
          )}
        >
          <Plus size={14} className="text-accent shrink-0" />
          {isOpen && <span className="text-text-secondary">New Chat</span>}
        </button>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '6px 8px', overflow: 'hidden' }}>
        <div className="space-y-0.5">
          {navItems.map(item => {
            const active = activeView === item.id
            const Icon = item.icon
            const badge = item.id === 'approvals' && status.pending_approvals > 0

            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={clsx(
                  "w-full flex items-center gap-2 rounded-lg transition-all relative",
                  isOpen ? "px-2.5 py-2" : "justify-center py-2",
                  active
                    ? "bg-accent/10 text-accent"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-2"
                )}
              >
                {active && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 rounded-r-full bg-accent"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
                <Icon size={16} className="shrink-0" />
                {isOpen && <span className="text-xs font-medium">{item.label}</span>}
                {badge && (
                  <span className={clsx(
                    "flex items-center justify-center min-w-[16px] h-[16px] rounded-full bg-warning text-surface-0 text-[9px] font-bold",
                    isOpen ? "ml-auto" : "absolute -top-0.5 -right-0.5"
                  )}>
                    {status.pending_approvals}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </nav>

      {/* Footer */}
      <div style={{ padding: '0 8px 10px', flexShrink: 0 }}>
        <div className={clsx(
          "flex items-center gap-2 rounded-lg bg-surface-2/50",
          isOpen ? "px-2.5 py-2" : "justify-center py-2"
        )}>
          <CircleDot size={8} className={clsx("shrink-0", status.live_mode ? "text-success" : "text-warning")} />
          {isOpen && (
            <span className="text-[10px] text-text-muted">
              {status.live_mode ? 'Live Azure' : 'Demo Mode'}
            </span>
          )}
        </div>
        {isOpen && status.tool_calls_count > 0 && (
          <div className="flex items-center gap-2 px-2.5 py-1.5 mt-1 rounded-lg bg-surface-2/50">
            <Activity size={8} className="text-accent shrink-0" />
            <span className="text-[10px] text-text-muted">{status.tool_calls_count} calls</span>
          </div>
        )}
      </div>
    </div>
  )
}
