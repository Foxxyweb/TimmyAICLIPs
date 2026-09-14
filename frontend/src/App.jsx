import { Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import Navbar from './components/Navbar'
import LoadingSpinner from './components/LoadingSpinner'

// Lazy load pages
const Home    = lazy(() => import('./pages/Home'))
const Results = lazy(() => import('./pages/Results'))
const History = lazy(() => import('./pages/History'))

function App() {
  return (
    <div className="min-h-screen bg-surface-900 bg-dots">
      <Navbar />
      <Suspense fallback={<LoadingSpinner fullscreen />}>
        <Routes>
          <Route path="/"               element={<Home />} />
          <Route path="/results/:jobId" element={<Results />} />
          <Route path="/history"        element={<History />} />
        </Routes>
      </Suspense>
    </div>
  )
}

export default App
