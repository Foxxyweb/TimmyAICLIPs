import { useEffect, useRef, useState, useCallback } from 'react'

const WS_BASE = `ws://${window.location.hostname}:8000`

/**
 * Custom hook untuk subscribe ke status job via WebSocket.
 * Otomatis reconnect jika koneksi terputus.
 * 
 * @param {string} jobId - ID job untuk di-track
 * @returns {{ job, isConnected, error }}
 */
export default function useJobStatus(jobId) {
  const [job, setJob]             = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError]         = useState(null)
  
  const wsRef         = useRef(null)
  const retryCount    = useRef(0)
  const retryTimerRef = useRef(null)
  const maxRetries    = 5

  const connect = useCallback(() => {
    if (!jobId) return
    
    // Cleanup existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    const wsUrl = `${WS_BASE}/api/ws/${jobId}`
    console.log(`🔌 Connecting WebSocket: ${wsUrl}`)
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      setIsConnected(true)
      setError(null)
      retryCount.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setJob(data)
        
        // Auto-disconnect setelah job selesai atau gagal
        if (data.status === 'completed' || data.status === 'failed') {
          console.log(`🏁 Job ${data.status}, closing WebSocket`)
          setTimeout(() => ws.close(), 1000)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setError('Koneksi terputus')
    }

    ws.onclose = (event) => {
      setIsConnected(false)
      console.log(`🔌 WebSocket closed (code: ${event.code})`)
      
      // Auto-reconnect jika bukan closed intentionally
      if (event.code !== 1000 && retryCount.current < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retryCount.current), 10000)
        console.log(`⏳ Reconnecting in ${delay}ms (attempt ${retryCount.current + 1}/${maxRetries})`)
        retryCount.current++
        retryTimerRef.current = setTimeout(connect, delay)
      }
    }
  }, [jobId])

  useEffect(() => {
    connect()
    
    return () => {
      // Cleanup on unmount
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
      if (wsRef.current) wsRef.current.close(1000, 'Component unmounted')
    }
  }, [connect])

  return { job, isConnected, error }
}
