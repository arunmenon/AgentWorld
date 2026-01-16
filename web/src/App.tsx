import { Routes, Route } from 'react-router-dom'
import { Shell } from './layouts/Shell'
import { ToastContainer, ConfirmDialog } from './components/ui'
import Dashboard from './pages/Dashboard'
import Simulations from './pages/Simulations'
import SimulationCreate from './pages/SimulationCreate'
import SimulationDetail from './pages/SimulationDetail'
import Personas from './pages/Personas'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

function App() {
  return (
    <>
      <Shell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/simulations" element={<Simulations />} />
          <Route path="/simulations/new" element={<SimulationCreate />} />
          <Route path="/simulations/:id" element={<SimulationDetail />} />
          <Route path="/personas" element={<Personas />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Shell>
      <ToastContainer />
      <ConfirmDialog />
    </>
  )
}

export default App
