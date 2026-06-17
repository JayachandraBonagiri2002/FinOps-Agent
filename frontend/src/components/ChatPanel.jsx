import { useState, useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react'
import ReactMarkdown from 'react-markdown'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Scan, TrendingUp, Trash2, Lightbulb,
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
    <div className="flex items-center gap-1.5 px-1 py-2">
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
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-accent/30 ml-1">
              {toolCalls.map((tc, i) => (
                <div key={i} className="pl-3 py-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-accent font-medium">{tc.tool}</span>
                    <span className="text-[10px] text-text-muted bg-surface-3 px-1.5 py-0.5 rounded">step {tc.iteration}</span>
                  </div>
                  {tc.arguments && Object.keys(tc.arguments).length > 0 && (
                    <div className="text-[11px] text-text-muted font-mono mt-1 break-all leading-relaxed">
                      {JSON.stringify(tc.arguments).slice(0, 120)}
                    </div>
                  )}
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
      initial={isLast ? { opacity: 0, y: 8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="w-full"
    >
      <div className={clsx(
        "flex gap-3 w-full",
        isUser ? "flex-row-reverse" : ""
      )}>
        {/* Avatar */}
        <div className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1",
          isUser ? "bg-accent/20" : "bg-surface-3"
        )}>
          {isUser ? <User size={15} className="text-accent" /> : <Bot size={15} className="text-text-secondary" />}
        </div>

        {/* Message content */}
        <div className={clsx(
          "min-w-0 rounded-2xl px-4 py-3 max-w-full",
          isUser
            ? "bg-accent/10 border border-accent/20 ml-12"
            : "bg-surface-1 border border-border-subtle mr-12"
        )}>
          {isUser ? (
            <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="message-content text-text-secondary">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          {!isUser && message.tool_calls && (
            <ToolCallsAccordion toolCalls={message.tool_calls} />
          )}
        </div>
      </div>
    </motion.div>
  )
}

const ChatPanel = forwardRef(function ChatPanel(props, ref) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

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
        setError('Azure APIs are rate-limited. Please wait 30 seconds and try again.')
        setLoading(false)
        return
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Server error (${res.status})`)
      }

      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        tool_calls: data.tool_calls,
        reasoning_steps: data.reasoning_steps,
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
    <div className="h-full flex flex-col">
      {/* Messages Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <div className="h-full flex flex-col items-center justify-center px-4">
            <div className="text-center w-full max-w-3xl">
              <div className="w-16 h-16 rounded-3xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-6">
                <Sparkles size={32} className="text-accent" />
              </div>
              <h1 className="text-3xl font-extrabold text-text-primary mb-3 tracking-tight">
                FinOps Copilot
              </h1>
              <p className="text-text-secondary text-base mb-10 leading-relaxed max-w-lg mx-auto">
                Ask me anything about your Azure costs, resources, and optimizations.
                <br />Connected to your live Azure environment.
              </p>
              <div className="grid grid-cols-2 gap-4 max-w-2xl mx-auto">
                {quickActions.map((action) => {
                  const Icon = action.icon
                  return (
                    <button
                      key={action.label}
                      onClick={() => sendMessage(action.message)}
                      className="flex items-center gap-3 p-4 rounded-2xl border border-border bg-surface-1 hover:bg-surface-2 hover:border-accent/40 hover:shadow-lg hover:shadow-accent/5 transition-all duration-200 text-left group"
                    >
                      <div className="w-10 h-10 rounded-xl bg-surface-3 flex items-center justify-center shrink-0 group-hover:bg-accent/10 group-hover:text-accent transition-colors">
                        <Icon size={18} className="text-text-muted group-hover:text-accent transition-colors" />
                      </div>
                      <div>
                        <span className="block text-sm font-semibold text-text-secondary group-hover:text-text-primary transition-colors">{action.label}</span>
                        <span className="block text-[11px] text-text-muted mt-0.5 line-clamp-1">{action.message}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-8 max-w-4xl mx-auto pb-6">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} isLast={i === messages.length - 1} />
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center shrink-0">
                  <Bot size={15} className="text-text-secondary" />
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
        )}
      </div>

      {/* Input Area */}
      <div className="relative shrink-0 border-t border-border-subtle glass-panel px-4 sm:px-6 lg:px-8 py-5 z-20 w-full">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-3 bg-surface-1/90 border border-border rounded-2xl px-4 py-3 focus-within:border-accent focus-within:shadow-[0_0_15px_rgba(96,165,250,0.15)] transition-all duration-300">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about costs, resources, or optimizations..."
              rows={1}
              className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-muted outline-none resize-none max-h-[140px] leading-relaxed"
              style={{ minHeight: '24px' }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className={clsx(
                "shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150",
                input.trim() && !loading
                  ? "bg-accent text-white hover:bg-accent/80 active:scale-95"
                  : "bg-surface-3 text-text-muted cursor-not-allowed"
              )}
            >
              <ArrowUp size={16} />
            </button>
          </div>
          <p className="text-[11px] text-text-muted text-center mt-2 opacity-60">
            Connected to live Azure APIs &bull; Results are real-time
          </p>
        </div>
      </div>
    </div>
  )
})

export default ChatPanel
