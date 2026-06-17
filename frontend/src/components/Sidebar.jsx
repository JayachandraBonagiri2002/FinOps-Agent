import { useState, useEffect } from 'react'
import {
  MessageSquare,
  BarChart3,
  ShieldCheck,
  Plus,
  PanelLeftClose,
  PanelLeft,
  Cloud,
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
    { id: 'dashboard', icon: BarChart3, label: 'Cost Dashboard' },
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
      <div className="w-16 bg-[#0f0f0f] border-r border-[#1a1a1a] flex flex-col h-full py-4">
        {/* Top actions */}
        <div className="flex flex-col items-center gap-1">
          <button
            onClick={onToggle}
            className="p-2.5 rounded-xl hover:bg-[#1e1e1e] text-gray-500 hover:text-gray-300 transition-all duration-200"
            title="Expand sidebar"
          >
            <PanelLeft size={18} />
          </button>
          <button
            onClick={handleNewChat}
            className="p-2.5 rounded-xl hover:bg-[#1e1e1e] text-gray-500 hover:text-gray-300 transition-all duration-200"
            title="New chat"
          >
            <Plus size={18} />
          </button>
        </div>

        {/* Divider */}
        <div className="mx-auto w-6 h-px bg-[#1a1a1a] my-2" />

        {/* Nav icons */}
        <div className="flex flex-col items-center gap-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`relative p-2.5 rounded-xl transition-all duration-200 ${
                activeView === item.id
                  ? 'bg-[#1e1e1e] text-white'
                  : 'text-gray-600 hover:bg-[#1a1a1a] hover:text-gray-400'
              }`}
              title={item.label}
            >
              <item.icon size={18} />
              {item.id === 'approvals' && status?.pending_approvals > 0 && (
                <span className="absolute -top-1 -right-1 min-w-[18px] h-5 bg-orange-600 rounded-full text-[9px] text-white flex items-center justify-center font-bold px-0.5 shadow-lg shadow-orange-600/50">
                  {status.pending_approvals}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Bottom status indicator */}
        <div className="mt-auto flex flex-col items-center gap-2">
          <div className="w-px h-6 bg-[#1a1a1a]" />
          <div className="p-1.5" title={status?.live_mode ? 'Connected to Azure' : 'Demo Mode'}>
            <CircleDot
              size={10}
              className={status?.live_mode ? 'text-green-500 drop-shadow-[0_0_3px_rgba(34,197,94,0.6)]' : 'text-yellow-500 drop-shadow-[0_0_3px_rgba(234,179,8,0.6)]'}
            />
          </div>
        </div>
      </div>
    )
  }

  // Expanded state
  return (
    <div className="w-64 bg-[#0f0f0f] flex flex-col h-full border-r border-[#1a1a1a]">
      {/* Header - toggle + new chat */}
      <div className="flex items-center justify-between px-4 pt-4 pb-3">
        <button
          onClick={onToggle}
          className="p-2 rounded-xl hover:bg-[#1e1e1e] text-gray-600 hover:text-gray-400 transition-all duration-200"
          title="Collapse sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
        <button
          onClick={handleNewChat}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 hover:text-emerald-300 text-xs font-semibold transition-all duration-200 border border-emerald-500/30 hover:border-emerald-500/50"
          title="New chat"
        >
          <Plus size={14} strokeWidth={2} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Section label */}
      <div className="px-4 pt-3 pb-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-600">
          Navigation
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 overflow-y-auto space-y-1">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
              activeView === item.id
                ? 'bg-[#1e1e1e] text-white shadow-sm'
                : 'text-gray-500 hover:bg-[#1a1a1a] hover:text-gray-300'
            }`}
          >
            {activeView === item.id && (
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-emerald-500 rounded-r-lg" />
            )}
            <item.icon size={16} strokeWidth={1.5} />
            <span className="truncate flex-1">{item.label}</span>
            {item.id === 'approvals' && status?.pending_approvals > 0 && (
              <span className="ml-auto bg-orange-600/25 text-orange-400 text-xs font-bold px-2 py-0.5 rounded-full border border-orange-500/30">
                {status.pending_approvals}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Divider */}
      <div className="mx-4 h-px bg-[#1a1a1a]" />

      {/* Footer - Connection Status Card */}
      <div className="px-3 pb-4 pt-4">
        <div className="bg-gradient-to-br from-[#1a1a1a] to-[#121212] rounded-2xl p-4 border border-[#1a1a1a] shadow-sm">
          {/* Connection badge */}
          <div className="flex items-center gap-2.5 mb-3">
            <div className={`flex items-center justify-center w-6 h-6 rounded-full ${
              status?.live_mode ? 'bg-green-500/20' : 'bg-yellow-500/20'
            }`}>
              <CircleDot
                size={11}
                className={status?.live_mode ? 'text-green-400' : 'text-yellow-400'}
              />
            </div>
            <span className={`text-xs font-semibold ${
              status?.live_mode ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {status?.live_mode ? 'Azure Connected' : 'Demo Mode'}
            </span>
          </div>

          {/* Divider */}
          <div className="w-full h-px bg-[#2a2a2a] mb-3" />

          {/* Session stats */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Tool calls</span>
              <span className="text-gray-300 font-mono font-semibold">
                {status?.tool_calls_count ?? 0}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Executed</span>
              <span className="text-gray-300 font-mono font-semibold">
                {status?.executed_actions ?? 0}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Pending</span>
              <span className={`font-mono font-semibold ${
                (status?.pending_approvals ?? 0) > 0 ? 'text-orange-400' : 'text-gray-300'
              }`}>
                {status?.pending_approvals ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Branding */}
        <div className="mt-3 flex items-center justify-center gap-2 px-2 py-2 rounded-lg bg-[#1a1a1a]/50">
          <Cloud size={12} className="text-gray-700" />
          <span className="text-xs text-gray-600 font-semibold tracking-wide">
            FinOps Copilot
          </span>
        </div>
      </div>
    </div>
  )
}
