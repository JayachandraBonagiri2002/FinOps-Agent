import { useState, useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react'
import ReactMarkdown from 'react-markdown'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Scan, TrendingUp, Trash2, Lightbulb,
  ChevronDown, ChevronRight, Wrench, Bot, User,
  Sparkles, ArrowUp
} from 'lucide-react'
import clsx from 'clsx'

const quickActions = [
  { icon: Scan, label: 'Full Scan', message: 'Run a comprehensive FinOps scan across all my subscriptions' },
  { icon: TrendingUp, label: 'Cost Trends', message: 'Show me cost trends for the past month with week-over-week comparison' },
  { icon: Trash2, label: 'Find Waste', message: 'Detect anomalies and find wasted resources I can clean up' },
  { icon: Lightbulb, label: 'Optimize', message: 'Give me optimization recommendations to reduce my Azure spend' },
]

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-1 py-3">
      {[0, 1, 2].map(i => (
        <motion.div
          key={i}
          className="w-2 h-2 rounded-full bg-accent"
          animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </div>
  )
}

function ToolCallsAccordion({ toolCalls }) {
  const [open, setOpen] = useState(false)
  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className="mt-3 pt-3 border-t border-border-subtle">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
      >
        <Wrench size={12} />
        <span>{toolCalls.length} tool{toolCalls.length > 1 ? 's' : ''} used</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1 pl-2 border-l-2 border-accent/30 ml-1">
              {toolCalls.map((tc, i) => (
                <div key={i} className="pl-3 py-1">
                  <span className="text-xs font-mono text-accent">{tc.tool}</span>
                  <span className="text-[10px] text-text-muted ml-2">step {tc.iteration}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function MessageBubble({ message, isLast }) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={isLast ? { opacity: 0, y: 6 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className="w-full"
    >
      <div className={clsx("flex gap-3", isUser && "flex-row-reverse")}>
        <div className={clsx(
          "w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5",
          isUser ? "bg-accent/15" : "bg-surface-3"
        )}>
          {isUser ? <User size={14} className="text-accent" /> : <Bot size={14} className="text-text-muted" />}
        </div>
        <div className={clsx(
          "min-w-0 rounded-xl px-4 py-3",
          isUser
            ? "bg-accent/8 border border-accent/20 max-w-[75%]"
            : "bg-surface-1 border border-border-subtle flex-1"
        )}>
          {isUser ? (
            <p className="text-[0.9rem] text-text-primary leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="message-content text-text-secondary">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          {!isUser && message.tool_calls && <ToolCallsAccordion toolCalls={message.tool_calls} />}
        </div>
      </div>
    </motion.div>
  )
}

const ChatPanel = forwardRef(function ChatPanel(_props, ref) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)

  useImperativeHandle(ref, () => ({
    resetChat() {
      setMessages([])
      setInput('')
      setError(null)
      setLoading(false)
      fetch('/api/conversation/reset', { method: 'POST' }).catch(() => {})
    }
  }))

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const sendMessage = useCallback(async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return

    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      })

      if (res.status === 429) {
        setError('Azure APIs are rate-limited. Wait 30 seconds and try again.')
        setLoading(false)
        return
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error ${res.status}`)
      }

      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        tool_calls: data.tool_calls,
      }])
    } catch (e) {
      setError(e.message || 'Failed to connect to backend.')
    } finally {
      setLoading(false)
    }
  }, [input, loading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const isEmpty = messages.length === 0

  return (
    <>
      {/* Scrollable messages area */}
      <div
        ref={scrollRef}
        style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}
      >
        {isEmpty ? (
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
            <div style={{ textAlign: 'center', width: '100%', maxWidth: 560 }}>
              <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-5">
                <Sparkles size={24} className="text-accent" />
              </div>
              <h1 className="text-2xl font-bold text-text-primary mb-2">FinOps Copilot</h1>
              <p className="text-text-muted text-sm mb-8 max-w-sm mx-auto">
                Ask anything about your Azure costs, resources, and optimizations.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {quickActions.map((action) => {
                  const Icon = action.icon
                  return (
                    <button
                      key={action.label}
                      onClick={() => sendMessage(action.message)}
                      className="flex items-center gap-2.5 p-3 rounded-xl border border-border bg-surface-1 hover:bg-surface-2 hover:border-accent/30 transition-all text-left group"
                    >
                      <Icon size={16} className="text-text-muted group-hover:text-accent shrink-0 transition-colors" />
                      <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">{action.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '24px 24px 16px', maxWidth: 860, margin: '0 auto' }}>
            <div className="space-y-5">
              {messages.map((msg, i) => (
                <MessageBubble key={i} message={msg} isLast={i === messages.length - 1} />
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-surface-3 flex items-center justify-center shrink-0">
                    <Bot size={14} className="text-text-muted" />
                  </div>
                  <TypingIndicator />
                </div>
              )}
              {error && (
                <div className="bg-danger/10 border border-danger/20 rounded-xl px-4 py-3 text-sm text-danger">
                  {error}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input bar — always at bottom */}
      <div
        className="glass-panel border-t border-border-subtle"
        style={{ flexShrink: 0, padding: '14px 24px' }}
      >
        <div style={{ maxWidth: 860, margin: '0 auto' }}>
          <div className="flex items-end gap-3 bg-surface-1 border border-border rounded-2xl px-4 py-3 focus-within:border-accent/50 transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about costs, resources, or optimizations..."
              rows={1}
              className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-muted outline-none resize-none leading-relaxed"
              style={{ minHeight: 22, maxHeight: 120 }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className={clsx(
                "shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all",
                input.trim() && !loading
                  ? "bg-accent text-white hover:bg-accent-muted active:scale-95"
                  : "bg-surface-3 text-text-muted cursor-not-allowed"
              )}
            >
              <ArrowUp size={16} />
            </button>
          </div>
          <p className="text-[10px] text-text-muted text-center mt-2 opacity-50">
            Connected to live Azure APIs
          </p>
        </div>
      </div>
    </>
  )
})

export default ChatPanel
