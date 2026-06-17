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
    if (inputRef.current) inputRef.current.style.height = '44px'

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      if (res.status === 429) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Rate limit exceeded. Please wait a moment and try again.', tool_calls: [] }])
      } else if (!res.ok) {
        const err = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.detail || 'Something went wrong'}`, tool_calls: [] }])
      } else {
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', content: data.response, tool_calls: data.tool_calls || [], reasoning_steps: data.reasoning_steps }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Failed to connect to the backend. Make sure the API server is running.', tool_calls: [] }])
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
    { icon: Scan, label: 'Full optimization scan', prompt: 'Run a full FinOps optimization scan across ALL subscriptions — detect all anomalies, check utilization, and recommend actions.' },
    { icon: TrendingUp, label: 'Cost trends', prompt: 'Show me cost trends for the last 2 weeks. Which resources are increasing?' },
    { icon: Trash2, label: 'Find waste', prompt: 'Find all orphaned, unused, or idle resources that are wasting money.' },
    { icon: Lightbulb, label: 'Recommendations', prompt: 'Give me all optimization recommendations — right-sizing, scheduling, Reserved Instances, and cleanup.' },
  ]

  const toggleTools = (idx) => {
    setExpandedTools(prev => ({ ...prev, [idx]: !prev[idx] }))
  }

  return (
    <div className="absolute inset-0 flex flex-col">
      {/* Scrollable area — takes all available space */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center p-4">
            <div className="w-full max-w-[720px] text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 mb-6 shadow-lg shadow-emerald-500/20">
                <Bot size={32} className="text-white" strokeWidth={1.5} />
              </div>
              <h1 className="text-3xl font-semibold text-white mb-2">How can I help with your cloud costs?</h1>
              <p className="text-[#888] mb-10 text-sm">Ask about Azure spend, resources, optimization, or run a scan.</p>
              <div className="grid grid-cols-2 gap-3 max-w-[560px] mx-auto">
                {quickActions.map((a, i) => (
                  <button key={i} onClick={() => sendMessage(a.prompt)} className="flex items-center gap-3 px-4 py-3 rounded-xl border border-[#222] bg-[#111] hover:bg-[#1a1a1a] hover:border-[#333] transition-colors text-left group">
                    <a.icon size={16} className="text-[#555] group-hover:text-emerald-400 transition-colors flex-shrink-0" />
                    <span className="text-sm text-[#999] group-hover:text-[#ccc] transition-colors">{a.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-[720px] mx-auto px-4 py-6">
            {messages.map((msg, idx) => (
              <div key={idx} className="mb-5">
                {msg.role === 'user' ? (
                  <div className="flex justify-end">
                    <div className="max-w-[85%] bg-[#1a1a1a] border border-[#222] rounded-2xl rounded-br-md px-4 py-2.5">
                      <p className="text-[14px] text-white leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mt-0.5">
                      <Bot size={14} className="text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="message-content text-[14px] text-[#ccc] leading-relaxed">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                      {msg.tool_calls && msg.tool_calls.length > 0 && (
                        <div className="mt-3">
                          <button onClick={() => toggleTools(idx)} className="flex items-center gap-1.5 text-xs text-[#555] hover:text-[#888] transition-colors">
                            {expandedTools[idx] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                            <Wrench size={11} />
                            <span>{msg.tool_calls.length} tool{msg.tool_calls.length > 1 ? 's' : ''}{msg.reasoning_steps ? ` • ${msg.reasoning_steps} steps` : ''}</span>
                          </button>
                          {expandedTools[idx] && (
                            <div className="mt-2 space-y-0.5 bg-[#0d0d0d] rounded-lg p-2 border border-[#1a1a1a] text-xs">
                              {msg.tool_calls.map((tc, tIdx) => (
                                <div key={tIdx} className="flex items-start gap-2 py-1 px-1.5">
                                  <span className="text-emerald-600 font-mono text-[10px] bg-emerald-500/10 px-1 py-0.5 rounded">{tc.iteration}</span>
                                  <span className="text-[#888] font-mono truncate">{tc.tool}</span>
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
            {loading && (
              <div className="flex gap-3 mb-5">
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <Bot size={14} className="text-white" />
                </div>
                <div className="flex items-center gap-2 py-1">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-[#555] rounded-full animate-[bounce_1.4s_infinite_0ms]"></div>
                    <div className="w-1.5 h-1.5 bg-[#555] rounded-full animate-[bounce_1.4s_infinite_200ms]"></div>
                    <div className="w-1.5 h-1.5 bg-[#555] rounded-full animate-[bounce_1.4s_infinite_400ms]"></div>
                  </div>
                  <span className="text-xs text-[#555]">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area — fixed at bottom */}
      <div className="flex-shrink-0 border-t border-[#1a1a1a] bg-[#0a0a0a] px-4 py-3">
        <div className="max-w-[720px] mx-auto">
          {messages.length > 0 && (
            <div className="flex justify-end mb-2">
              <button onClick={handleNewChat} className="flex items-center gap-1.5 text-[11px] text-[#555] hover:text-[#888] transition-colors">
                <RotateCcw size={11} />
                New chat
              </button>
            </div>
          )}
          <div className="relative flex items-end bg-[#111] border border-[#222] rounded-2xl focus-within:border-[#333] transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message FinOps Copilot..."
              rows={1}
              className="flex-1 bg-transparent text-white text-[14px] pl-4 pr-12 py-3 resize-none outline-none placeholder-[#555] max-h-[120px] rounded-2xl"
              style={{ minHeight: '44px' }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-2 p-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:bg-[#222] disabled:text-[#555] disabled:cursor-not-allowed transition-colors"
            >
              {loading ? <CircleStop size={16} /> : <Send size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
