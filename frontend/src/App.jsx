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
    <div className="absolute inset-0 flex overflow-hidden bg-surface-0 text-text-primary font-sans antialiased">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onNewChat={handleNewChat}
      />
      <main className="flex-1 min-w-0 h-full relative bg-surface-0 w-full">
        {/* All panels stay mounted to preserve state — only visibility changes */}
        <div className={activeView === 'chat' ? 'h-full w-full' : 'hidden'}>
          <ChatPanel ref={chatRef} />
        </div>
        <div className={activeView === 'dashboard' ? 'h-full w-full overflow-y-auto' : 'hidden'}>
          <Dashboard />
        </div>
        <div className={activeView === 'approvals' ? 'h-full w-full overflow-y-auto' : 'hidden'}>
          <Approvals />
        </div>
      </main>
    </div>
  )
}

export default App
