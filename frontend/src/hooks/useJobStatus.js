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

  // Fungsi update pintar: jangan izinkan status mundur ke belakang
  const safeSetJob = useCallback((newData) => {
    if (!newData) return
    setJob((prev) => {
      if (!prev) return newData

      // Jika data baru progressnya lebih kecil dan statusnya sama, abaikan agar tidak kedap-kedip
      if (newData.progress < prev.progress && newData.status === prev.status) {
        return prev
      }

      // Gabungkan data agar properti video_title / thumbnail tidak hilang mendadak
      return {
        ...prev,
        ...newData,
        video_title: newData.video_title || prev.video_title,
        thumbnail_url: newData.thumbnail_url || prev.thumbnail_url,
      }
    })
  }, [])

  // 1. Polling HTTP
  const fetchJobStatus = useCallback(async () => {
    if (!jobId) return
    try {
      const res = await axios.get(`${API_BASE}/api/jobs/${jobId}`, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      })
      if (res.data) {
        safeSetJob(res.data)
        return res.data
      }
    } catch (err) {
      console.error('Fetch job error:', err)
    }
  }, [jobId, safeSetJob])

  useEffect(() => {
    if (!jobId) return

    fetchJobStatus()

    const interval = setInterval(async () => {
      const data = await fetchJobStatus()
      if (data && (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled')) {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId, fetchJobStatus])

  // 2. WebSocket
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
        safeSetJob(data)
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
  }, [jobId, safeSetJob])

  useEffect(() => {
    connect()
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
      if (wsRef.current) wsRef.current.close(1000, 'Component unmounted')
    }
  }, [connect])

  return { job, isConnected, error }
}