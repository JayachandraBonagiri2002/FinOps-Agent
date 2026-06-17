import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import Dashboard from './components/Dashboard'
import Approvals from './components/Approvals'

function App() {
  const [activeView, setActiveView] = useState('chat')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-[#0f0f0f]">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <main className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-[#0f0f0f] via-[#0f0f0f] to-[#1a1a1a]">
        {activeView === 'chat' && <ChatPanel />}
        {activeView === 'dashboard' && <Dashboard />}
        {activeView === 'approvals' && <Approvals />}
      </main>
    </div>
  )
}

export default App
