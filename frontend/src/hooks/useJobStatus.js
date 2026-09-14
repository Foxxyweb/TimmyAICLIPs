import { useEffect, useRef, useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function useJobStatus(jobId) {
  const [job, setJob]                 = useState(null)
  const [isConnected, setIsConnected] = useState(true)
  const [error, setError]             = useState(null)
  const isFinished                    = useRef(false)

  const fetchJobStatus = useCallback(async () => {
    if (!jobId || isFinished.current) return
    try {
      const res = await axios.get(`${API_BASE}/api/jobs/${jobId}`, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      })
      
      const data = res.data
      if (!data) return

      // Update state dengan aman: jangan izinkan progress mundur ke belakang
      setJob((prev) => {
        if (!prev) return data
        
        // Kunci progress agar selalu maju dan tidak berkedip turun
        const higherProgress = Math.max(prev.progress || 0, data.progress || 0)
        
        return {
          ...prev,
          ...data,
          progress: higherProgress,
          video_title: data.video_title || prev.video_title,
          thumbnail_url: data.thumbnail_url || prev.thumbnail_url,
          status_message: data.status_message || prev.status_message,
        }
      })

      setIsConnected(true)
      setError(null)

      // Berhenti polling jika status sudah selesai atau gagal
      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        isFinished.current = true
      }
    } catch (err) {
      console.error('Fetch job error:', err)
      // Jangan langsung buat layar blank jika cuma transient error ngrok
      setIsConnected(false)
    }
  }, [jobId])

  useEffect(() => {
    if (!jobId) return

    isFinished.current = false
    fetchJobStatus()

    // Polling stabil tiap 2 detik tanpa WebSocket yang tabrakan
    const interval = setInterval(() => {
      if (!isFinished.current) {
        fetchJobStatus()
      } else {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId, fetchJobStatus])

  return { job, isConnected, error }
}