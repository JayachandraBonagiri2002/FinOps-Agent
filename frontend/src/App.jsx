import { useState, useCallback, useRef } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import Dashboard from './components/Dashboard'
import Approvals from './components/Approvals'

function App() {
  const [activeView, setActiveView] = useState('chat')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const chatRef = useRef(null)

  const handleNewChat = useCallback(() => {
    if (chatRef.current) chatRef.current.resetChat()
    setActiveView('chat')
  }, [])

  return (
    <div
      id="app-shell"
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        overflow: 'hidden',
        background: 'var(--color-surface-0, #0a0a0c)',
      }}
    >
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onNewChat={handleNewChat}
      />

      {/* Main content area — flex:1 takes remaining width after sidebar */}
      <div style={{ flex: 1, minWidth: 0, height: '100%', position: 'relative' }}>
        {/*
          All three views are ALWAYS mounted (never unmounted).
          We use display:none to hide inactive ones.
          This preserves all state (chat messages, dashboard data, etc.)
        */}
        <div
          id="view-chat"
          style={{
            position: 'absolute',
            inset: 0,
            display: activeView === 'chat' ? 'flex' : 'none',
            flexDirection: 'column',
          }}
        >
          <ChatPanel ref={chatRef} />
        </div>

        <div
          id="view-dashboard"
          style={{
            position: 'absolute',
            inset: 0,
            display: activeView === 'dashboard' ? 'block' : 'none',
            overflowY: 'auto',
          }}
        >
          <Dashboard />
        </div>

        <div
          id="view-approvals"
          style={{
            position: 'absolute',
            inset: 0,
            display: activeView === 'approvals' ? 'block' : 'none',
            overflowY: 'auto',
          }}
        >
          <Approvals />
        </div>
      </div>
    </div>
  )
}

export default App
