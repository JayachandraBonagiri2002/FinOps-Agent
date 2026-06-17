import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Send,
  Scan,
  TrendingUp,
  Trash2,
  Lightbulb,
  Wrench,
  ChevronDown,
  ChevronRight,
  Bot,
  CircleStop,
  RotateCcw,
} from 'lucide-react'

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedTools, setExpandedTools] = useState({})
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return

    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    if (inputRef.current) {
      inputRef.current.style.height = '52px'
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })

      if (res.status === 429) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Rate limit exceeded. Please wait a moment and try again.',
          tool_calls: [],
        }])
      } else if (!res.ok) {
        const err = await res.json()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${err.detail || 'Something went wrong'}`,
          tool_calls: [],
        }])
      } else {
        const data = await res.json()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          tool_calls: data.tool_calls || [],
          reasoning_steps: data.reasoning_steps,
        }])
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to connect to the backend. Make sure the API server is running.',
        tool_calls: [],
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleNewChat = () => {
    fetch('/api/conversation/reset', { method: 'POST' })
    setMessages([])
    setExpandedTools({})
  }

  const quickActions = [
    { icon: Scan, label: 'Run a full optimization scan', description: 'Detect anomalies, check utilization across all subscriptions', prompt: 'Run a full FinOps optimization scan across ALL subscriptions — detect all anomalies, check utilization, and recommend actions.' },
    { icon: TrendingUp, label: 'Show cost trends', description: 'Analyze spending patterns over the last 2 weeks', prompt: 'Show me cost trends for the last 2 weeks. Which resources are increasing?' },
    { icon: Trash2, label: 'Find wasted resources', description: 'Identify orphaned, unused, or idle resources', prompt: 'Find all orphaned, unused, or idle resources that are wasting money.' },
    { icon: Lightbulb, label: 'Get recommendations', description: 'Right-sizing, scheduling, RI, and cleanup suggestions', prompt: 'Give me all optimization recommendations — right-sizing, scheduling, Reserved Instances, and cleanup.' },
  ]

  const toggleTools = (idx) => {
    setExpandedTools(prev => ({ ...prev, [idx]: !prev[idx] }))
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-gradient-to-b from-[#0f0f0f] to-[#1a1a1a]">
      {/* Header bar - clean & minimal */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-[#2a2a2a]/50 bg-[#0f0f0f]/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center">
            <span className="text-xs font-bold text-white">FC</span>
          </div>
          <div>
            <div className="text-sm font-semibold text-white">FinOps Copilot</div>
            <div className="text-xs text-gray-500">GPT-4.1-mini</div>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-200 transition-colors px-3 py-1.5 rounded-lg hover:bg-[#1e1e1e] border border-[#2a2a2a] hover:border-[#3a3a3a]"
          >
            <RotateCcw size={13} />
            <span>New chat</span>
          </button>
        )}
      </div>

      {/* Main content area - scrollable messages OR empty state */}
      <div className="flex-1 overflow-y-auto flex flex-col">
        {messages.length === 0 ? (
          /* ===== EMPTY STATE ===== */
          <div className="flex-1 flex flex-col items-center justify-center px-6 lg:px-12 xl:px-24 pb-[160px]">
            <div className="w-full flex flex-col items-center">
              {/* Icon with gradient glow */}
              <div className="relative mb-8">
                <div className="absolute inset-0 w-20 h-20 rounded-full bg-gradient-to-r from-emerald-500/40 via-cyan-500/30 to-blue-500/20 blur-2xl animate-pulse"></div>
                <div className="relative w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-600 flex items-center justify-center shadow-2xl shadow-emerald-500/40">
                  <Bot size={36} className="text-white" strokeWidth={1.5} />
                </div>
              </div>

              {/* Title */}
              <h1 className="text-4xl font-bold text-white mb-3 text-center tracking-tight">
                How can I help optimize your cloud costs?
              </h1>

              {/* Subtitle */}
              <p className="text-base text-gray-400 text-center mb-12 leading-relaxed max-w-2xl">
                Ask me anything about your Azure spend, waste detection, cost trends, resource optimization, or run a full scan.
              </p>

              {/* Quick action cards - improved grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4 w-full max-w-7xl">
                {quickActions.map((action, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(action.prompt)}
                    className="flex flex-col items-start gap-3 p-5 rounded-2xl bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#222] transition-all duration-300 text-left group cursor-pointer hover:shadow-xl hover:shadow-black/20"
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 group-hover:from-emerald-500/30 group-hover:to-cyan-500/30 transition-colors">
                        <action.icon size={18} className="text-emerald-400 group-hover:text-emerald-300 transition-colors" />
                      </div>
                      <span className="text-sm font-semibold text-gray-100 group-hover:text-white transition-colors flex-1">{action.label}</span>
                    </div>
                    <span className="text-xs text-gray-500 leading-relaxed group-hover:text-gray-400 transition-colors">{action.description}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* ===== CHAT MESSAGES ===== */
          <div className="flex-1 overflow-y-auto">
            <div className="w-full py-6 px-6 lg:px-12 xl:px-24">
              {messages.map((msg, idx) => (
                <div key={idx} className="mb-6 max-w-7xl mx-auto">
                  {msg.role === 'user' ? (
                    /* User message */
                    <div className="flex justify-end">
                      <div className="max-w-[70%]">
                        <div className="bg-[#2a2a2a] rounded-2xl px-6 py-3.5 border border-[#3a3a3a] shadow-sm">
                          <p className="text-sm sm:text-base text-white leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Assistant message */
                    <div className="flex gap-3 sm:gap-4">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center shadow-sm shadow-emerald-500/30">
                          <Bot size={16} className="text-white" strokeWidth={1.5} />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="message-content text-sm sm:text-base text-gray-300 leading-relaxed">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>

                        {msg.tool_calls && msg.tool_calls.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-[#2a2a2a]">
                            <button
                              onClick={() => toggleTools(idx)}
                              className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300 transition-colors py-1.5 px-2.5 rounded-lg hover:bg-[#1a1a1a] -ml-2.5"
                            >
                              {expandedTools[idx] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                              <Wrench size={12} className="text-gray-600" />
                              <span className="font-medium">
                                {msg.tool_calls.length} tool{msg.tool_calls.length > 1 ? 's' : ''}
                                {msg.reasoning_steps ? ` • ${msg.reasoning_steps} steps` : ''}
                              </span>
                            </button>
                            {expandedTools[idx] && (
                              <div className="mt-3 ml-0 space-y-1 bg-[#0d0d0d] rounded-xl p-3 border border-[#1a1a1a]">
                                {msg.tool_calls.map((tc, tIdx) => (
                                  <div key={tIdx} className="flex items-start gap-2 py-1.5 px-2 rounded text-xs">
                                    <span className="text-emerald-500/70 font-mono font-semibold text-[10px] bg-emerald-500/10 px-1.5 py-0.5 rounded flex-shrink-0">
                                      #{tc.iteration}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                      <div className="text-gray-300 font-mono">{tc.tool}</div>
                                      <div className="text-gray-600 font-mono truncate mt-0.5">
                                        {JSON.stringify(tc.arguments).slice(0, 100)}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {loading && (
                <div className="mb-6 max-w-7xl mx-auto">
                  <div className="flex gap-3 sm:gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center shadow-sm shadow-emerald-500/30">
                        <Bot size={16} className="text-white" strokeWidth={1.5} />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 py-1">
                      <div className="flex gap-1.5">
                        <div className="w-2 h-2 bg-emerald-400/80 rounded-full animate-[bounce_1.4s_infinite_0ms]"></div>
                        <div className="w-2 h-2 bg-emerald-400/80 rounded-full animate-[bounce_1.4s_infinite_200ms]"></div>
                        <div className="w-2 h-2 bg-emerald-400/80 rounded-full animate-[bounce_1.4s_infinite_400ms]"></div>
                      </div>
                      <span className="text-xs text-gray-500 font-medium">Analyzing your request...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* ===== INPUT BAR - sticky at bottom ===== */}
        <div className="flex-shrink-0 bg-gradient-to-t from-[#0f0f0f] via-[#0f0f0f]/95 to-[#0f0f0f]/0 border-t border-[#1a1a1a] px-6 lg:px-12 xl:px-24 pt-6 pb-6">
          <div className="w-full max-w-7xl mx-auto">
            <div className="relative bg-[#1e1e1e] rounded-2xl border border-[#2a2a2a] focus-within:border-[#3a3a3a] focus-within:shadow-lg focus-within:shadow-emerald-500/10 transition-all duration-300">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about your cloud costs..."
                rows={1}
                className="w-full bg-transparent text-white text-sm sm:text-base pl-5 pr-14 py-3.5 sm:py-4 resize-none outline-none placeholder-gray-600 max-h-[160px] rounded-2xl"
                style={{ minHeight: '48px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
                }}
              />
              <button
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || loading}
                className="absolute right-3 bottom-3 p-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/30"
              >
                {loading ? <CircleStop size={18} /> : <Send size={18} strokeWidth={2} />}
              </button>
            </div>
            <p className="text-center text-xs text-gray-600 mt-2.5">
              FinOps Copilot can make mistakes. Always verify actions before approving.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
