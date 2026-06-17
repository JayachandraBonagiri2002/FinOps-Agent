import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import Dashboard from './components/Dashboard'
import Approvals from './components/Approvals'

function App() {
  const [activeView, setActiveView] = useState('chat')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-full w-full bg-[#0a0a0a] text-white">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <main className="flex-1 min-w-0 relative">
        <div className={`absolute inset-0 ${activeView === 'chat' ? '' : 'hidden'}`}>
          <ChatPanel />
        </div>
        <div className={`absolute inset-0 overflow-y-auto ${activeView === 'dashboard' ? '' : 'hidden'}`}>
          <Dashboard />
        </div>
        <div className={`absolute inset-0 overflow-y-auto ${activeView === 'approvals' ? '' : 'hidden'}`}>
          <Approvals />
        </div>
      </main>
    </div>
  )
}

export default App
