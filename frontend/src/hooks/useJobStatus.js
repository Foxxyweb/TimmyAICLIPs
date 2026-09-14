import { useEffect, useRef, useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const WS_BASE = API_BASE 
  ? API_BASE.replace(/^http/, 'ws') 
  : `ws://${window.location.hostname}:8000`

export default function useJobStatus(jobId) {
  const [job, setJob]                 = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError]             = useState(null)
  
  const wsRef         = useRef(null)
  const retryCount    = useRef(0)
  const retryTimerRef = useRef(null)
  const maxRetries    = 5

  // 1. Fungsi Fetch Manual (HTTP Polling Fallback)
  const fetchJobStatus = useCallback(async () => {
    if (!jobId) return
    try {
      const res = await axios.get(`${API_BASE}/api/jobs/${jobId}`, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      })
      setJob(res.data)
      return res.data
    } catch (err) {
      console.error('Fetch job error:', err)
    }
  }, [jobId])

  // 2. Polling setiap 2.5 detik selama job belum selesai/gagal
  useEffect(() => {
    if (!jobId) return

    fetchJobStatus()

    const interval = setInterval(async () => {
      const data = await fetchJobStatus()
      if (data && (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled')) {
        clearInterval(interval)
      }
    }, 2500)

    return () => clearInterval(interval)
  }, [jobId, fetchJobStatus])

  // 3. WebSocket Connection
  const connect = useCallback(() => {
    if (!jobId) return
    
    if (wsRef.current) {
      wsRef.current.close()
    }

    const wsUrl = `${WS_BASE}/api/ws/${jobId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setError(null)
      retryCount.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setJob(data)
        if (data.status === 'completed' || data.status === 'failed') {
          setTimeout(() => ws.close(), 1000)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = () => {
      setError('Koneksi terputus')
    }

    ws.onclose = (event) => {
      setIsConnected(false)
      if (event.code !== 1000 && retryCount.current < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retryCount.current), 10000)
        retryCount.current++
        retryTimerRef.current = setTimeout(connect, delay)
      }
    }
  }, [jobId])

  useEffect(() => {
    connect()
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
      if (wsRef.current) wsRef.current.close(1000, 'Component unmounted')
    }
  }, [connect])

  return { job, isConnected, error }
}