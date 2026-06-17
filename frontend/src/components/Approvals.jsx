import { useState, useEffect } from 'react'
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle, Loader2, Terminal } from 'lucide-react'

export default function Approvals() {
  const [approvals, setApprovals] = useState([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)

  const fetchApprovals = () => {
    fetch('/api/approvals')
      .then(r => r.json())
      .then(d => setApprovals(d.approvals || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchApprovals() }, [])

  const handleAction = async (index, action) => {
    setActing(index)
    try {
      await fetch('/api/approvals/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index, action }),
      })
      fetchApprovals()
    } catch {
      // ignore
    } finally {
      setActing(null)
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-500" size={32} />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-b from-[#0f0f0f] to-[#1a1a1a]">
      <div className="w-full max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-lg bg-green-500/20">
            <ShieldCheck size={20} className="text-green-400" strokeWidth={1.5} />
          </div>
          <h1 className="text-3xl font-bold text-white">Approval Queue</h1>
        </div>
        <p className="text-gray-500 text-sm mb-8">
          Actions below require your approval before execution. The agent determined these are too risky to auto-execute.
        </p>

        {approvals.length === 0 ? (
          <div className="bg-gradient-to-br from-[#1a1a1a] to-[#121212] rounded-2xl border border-[#1a1a1a] p-16 text-center shadow-sm">
            <ShieldCheck size={56} className="text-green-500/25 mx-auto mb-6" strokeWidth={1} />
            <p className="text-gray-300 text-lg font-semibold">No pending approvals</p>
            <p className="text-gray-500 text-sm mt-3">
              Run the agent to generate optimization actions that need your review.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {approvals.map((approval, i) => (
              <div
                key={i}
                className="bg-gradient-to-br from-[#1a1a1a] to-[#121212] rounded-2xl border border-[#1a1a1a] overflow-hidden hover:border-[#2a2a2a] transition-all shadow-sm"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        approval.risk_level === 'high'
                          ? 'bg-red-600/20'
                          : 'bg-orange-600/20'
                      }`}>
                        <ShieldAlert size={20} className={approval.risk_level === 'high' ? 'text-red-400' : 'text-orange-400'} strokeWidth={1.5} />
                      </div>
                      <div>
                        <h3 className="text-white font-semibold text-base">{approval.action}</h3>
                        <p className="text-gray-500 text-xs font-mono mt-0.5">{approval.resource_name}</p>
                      </div>
                    </div>
                    <span className={`text-xs px-3 py-1 rounded-full font-bold whitespace-nowrap ml-2 ${
                      approval.risk_level === 'high'
                        ? 'bg-red-600/20 text-red-400 border border-red-500/30'
                        : 'bg-orange-600/20 text-orange-400 border border-orange-500/30'
                    }`}>
                      {approval.risk_level?.toUpperCase() || 'MEDIUM'}
                    </span>
                  </div>

                  {approval.az_command && (
                    <div className="bg-[#0d0d0d] rounded-xl p-3 flex items-start gap-3 mb-4 border border-[#1a1a1a]">
                      <Terminal size={14} className="text-gray-700 mt-1 flex-shrink-0" strokeWidth={1.5} />
                      <code className="text-xs text-gray-400 font-mono break-all leading-relaxed flex-1">{approval.az_command}</code>
                    </div>
                  )}

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleAction(i, 'approve')}
                      disabled={acting === i}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-green-600/20"
                    >
                      {acting === i ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} strokeWidth={1.5} />}
                      Approve
                    </button>
                    <button
                      onClick={() => handleAction(i, 'reject')}
                      disabled={acting === i}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#2a2a2a] hover:bg-[#333] text-gray-300 text-sm font-semibold transition-all duration-200 border border-[#3a3a3a] disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      <XCircle size={16} strokeWidth={1.5} />
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
