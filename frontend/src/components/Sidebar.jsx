import { useState, useEffect } from 'react'
import {
  MessageSquare,
  BarChart3,
  ShieldCheck,
  PanelLeftClose,
  PanelLeft,
  CircleDot,
} from 'lucide-react'

export default function Sidebar({ activeView, setActiveView, isOpen, onToggle }) {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(setStatus)
      .catch(() => {})
  }, [activeView])

  const navItems = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'dashboard', icon: BarChart3, label: 'Dashboard' },
    { id: 'approvals', icon: ShieldCheck, label: 'Approvals' },
  ]

  const handleNewChat = () => {
    fetch('/api/conversation/reset', { method: 'POST' })
    setActiveView('chat')
    window.location.reload()
  }

  // Collapsed state
  if (!isOpen) {
    return (
      <div className="w-14 bg-[#0a0a0a] border-r border-[#1a1a1a] flex flex-col h-full">
        {/* Toggle button */}
        <div className="flex items-center justify-center py-4">
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-[#1a1a1a] text-[#6b7280] hover:text-white transition-colors duration-150"
            title="Expand sidebar"
          >
            <PanelLeft size={18} />
          </button>
        </div>

        {/* Nav icons */}
        <div className="flex flex-col items-center gap-1 px-2 mt-2">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`relative w-10 h-10 flex items-center justify-center rounded-lg transition-colors duration-150 ${
                activeView === item.id
                  ? 'bg-[#1a1a1a] text-white'
                  : 'text-[#6b7280] hover:bg-[#1a1a1a] hover:text-white'
              }`}
              title={item.label}
            >
              {activeView === item.id && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-emerald-500 rounded-r" />
              )}
              <item.icon size={18} />
              {item.id === 'approvals' && status?.pending_approvals > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-orange-500 rounded-full text-[9px] text-white flex items-center justify-center font-bold px-0.5">
                  {status.pending_approvals}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Bottom status dot */}
        <div className="mt-auto flex flex-col items-center pb-4">
          <div className="w-6 h-px bg-[#1a1a1a] mb-3" />
          <div title={status?.live_mode ? 'Azure Connected' : 'Demo Mode'}>
            <CircleDot
              size={10}
              className={status?.live_mode
                ? 'text-emerald-500'
                : 'text-yellow-500'
              }
            />
          </div>
        </div>
      </div>
    )
  }

  // Expanded state
  return (
    <div className="w-60 bg-[#0a0a0a] flex flex-col h-full border-r border-[#1a1a1a]">
      {/* Header - toggle + brand */}
      <div className="flex items-center gap-3 px-3 py-4">
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-[#1a1a1a] text-[#6b7280] hover:text-white transition-colors duration-150"
          title="Collapse sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
        <span className="text-sm font-semibold text-white tracking-tight">
          FinOps Copilot
        </span>
      </div>

      {/* Section label */}
      <div className="px-4 pt-4 pb-2">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-[#6b7280]">
          Navigation
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 overflow-y-auto space-y-0.5">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`relative w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 ${
              activeView === item.id
                ? 'bg-[#1a1a1a] text-white'
                : 'text-[#6b7280] hover:bg-[#1a1a1a] hover:text-white'
            }`}
          >
            {activeView === item.id && (
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-emerald-500 rounded-r" />
            )}
            <item.icon size={16} strokeWidth={1.5} />
            <span className="truncate flex-1 text-left">{item.label}</span>
            {item.id === 'approvals' && status?.pending_approvals > 0 && (
              <span className="ml-auto bg-orange-500/20 text-orange-400 text-xs font-bold px-1.5 py-0.5 rounded-full">
                {status.pending_approvals}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Divider */}
      <div className="mx-4 h-px bg-[#1a1a1a]" />

      {/* Footer - Status */}
      <div className="px-3 py-4">
        <div className="flex items-center gap-2 mb-3">
          <CircleDot
            size={10}
            className={status?.live_mode ? 'text-emerald-500' : 'text-yellow-500'}
          />
          <span className={`text-xs font-medium ${
            status?.live_mode ? 'text-emerald-400' : 'text-yellow-400'
          }`}>
            {status?.live_mode ? 'Azure Connected' : 'Demo Mode'}
          </span>
        </div>
        <div className="space-y-1.5 pl-[18px]">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#6b7280]">Tool calls:</span>
            <span className="text-gray-300 font-mono">
              {status?.tool_calls_count ?? 0}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#6b7280]">Pending:</span>
            <span className={`font-mono ${
              (status?.pending_approvals ?? 0) > 0 ? 'text-orange-400' : 'text-gray-300'
            }`}>
              {status?.pending_approvals ?? 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
