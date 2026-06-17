import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldCheck, ShieldAlert, CheckCircle2, XCircle,
  Loader2, Terminal, AlertTriangle, Clock
} from 'lucide-react'
import clsx from 'clsx'

function RiskBadge({ level }) {
  const cfg = {
    HIGH: { cls: 'bg-danger/10 text-danger border-danger/20', Icon: ShieldAlert },
    MEDIUM: { cls: 'bg-warning/10 text-warning border-warning/20', Icon: AlertTriangle },
    LOW: { cls: 'bg-success/10 text-success border-success/20', Icon: ShieldCheck },
  }
  const c = cfg[level?.toUpperCase()] || cfg.MEDIUM
  return (
    <span className={clsx("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border", c.cls)}>
      <c.Icon size={10} />
      {level || 'MEDIUM'}
    </span>
  )
}

function ApprovalCard({ approval, index, onAction }) {
  const [acting, setActing] = useState(null)

  const handle = async (action) => {
    setActing(action)
    await onAction(index, action)
    setActing(null)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20, height: 0 }}
      transition={{ duration: 0.2 }}
      className="bg-surface-1 border border-border-subtle rounded-xl p-4 hover:border-border transition-colors"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <RiskBadge level={approval.risk_level} />
            <span className="text-[10px] text-text-muted flex items-center gap-1">
              <Clock size={9} /> Pending
            </span>
          </div>
          <h3 className="text-sm font-semibold text-text-primary">
            {approval.action?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </h3>
          <p className="text-xs text-text-secondary mt-0.5 truncate">{approval.resource_name}</p>
        </div>
      </div>

      {approval.az_command && (
        <div className="bg-surface-0 border border-border-subtle rounded-lg p-3 mb-3 overflow-x-auto">
          <div className="flex items-center gap-1.5 mb-1 text-text-muted">
            <Terminal size={10} />
            <span className="text-[9px] uppercase tracking-wider font-medium">Azure CLI</span>
          </div>
          <code className="text-[11px] font-mono text-accent/80 break-all leading-relaxed">{approval.az_command}</code>
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={() => handle('approve')}
          disabled={acting !== null}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-success/10 text-success border border-success/20 hover:bg-success/20 active:scale-[0.98] transition-all disabled:opacity-50"
        >
          {acting === 'approve' ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle2 size={12} />}
          Approve
        </button>
        <button
          onClick={() => handle('reject')}
          disabled={acting !== null}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20 active:scale-[0.98] transition-all disabled:opacity-50"
        >
          {acting === 'reject' ? <Loader2 size={12} className="animate-spin" /> : <XCircle size={12} />}
          Reject
        </button>
      </div>
    </motion.div>
  )
}

export default function Approvals() {
  const [approvals, setApprovals] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchApprovals = useCallback(async () => {
    try {
      const res = await fetch('/api/approvals')
      if (res.ok) {
        const d = await res.json()
        setApprovals(d.approvals || [])
      }
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchApprovals()
    const interval = setInterval(fetchApprovals, 10000)
    return () => clearInterval(interval)
  }, [fetchApprovals])

  const handleAction = async (index, action) => {
    try {
      const res = await fetch('/api/approvals/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index, action }),
      })
      if (res.ok) {
        setApprovals(prev => prev.filter((_, i) => i !== index))
      }
    } catch {
      // silent
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={20} className="text-accent animate-spin" />
      </div>
    )
  }

  return (
    <div className="w-full p-4 sm:p-6 lg:p-8 xl:p-10 space-y-5 sm:space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight flex items-center gap-2">
          <ShieldCheck size={24} className="text-accent" />
          Pending Approvals
        </h1>
        <p className="text-[11px] text-text-muted mt-0.5">
          Review and approve risky actions before execution
        </p>
      </div>

      {approvals.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-14 h-14 rounded-xl bg-success/10 border border-success/20 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={24} className="text-success" />
          </div>
          <h2 className="text-base font-semibold text-text-primary mb-1">All Clear</h2>
          <p className="text-xs text-text-muted">No pending approvals. Risky actions will appear here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {approvals.map((a, i) => (
              <ApprovalCard key={`${a.resource_name}-${i}`} approval={a} index={i} onAction={handleAction} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
