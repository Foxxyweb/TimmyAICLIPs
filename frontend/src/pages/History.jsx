import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, ArrowRight, Video, Calendar, AlertCircle, RefreshCw } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function History() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const fetchJobs = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/api/jobs`, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      })

      // Penanganan aman untuk mencegah x.map is not a function
      if (Array.isArray(res.data)) {
        setJobs(res.data)
      } else if (res.data && Array.isArray(res.data.jobs)) {
        setJobs(res.data.jobs)
      } else if (res.data && Array.isArray(res.data.items)) {
        setJobs(res.data.items)
      } else {
        setJobs([])
      }
    } catch (err) {
      console.error('Fetch history error:', err)
      setError('Gagal memuat riwayat job.')
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  return (
    <main className="min-h-screen py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Clock className="w-6 h-6 text-brand-400" /> Riwayat Job
            </h1>
            <p className="text-white/40 text-sm mt-1">Daftar video yang telah diproses sebelumnya</p>
          </div>
          <button
            onClick={fetchJobs}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-white/40">
            <RefreshCw className="w-8 h-8 animate-spin mb-3 text-brand-400" />
            <p className="text-sm">Memuat riwayat...</p>
          </div>
        ) : error ? (
          <div className="glass-card p-6 border-red-500/20 bg-red-500/5 text-center text-white/70">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 text-red-400" />
            <p className="text-sm">{error}</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="glass-card p-12 text-center text-white/40">
            <Video className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-base font-medium text-white/60">Belum ada video yang diproses</p>
            <p className="text-xs mt-1">Kembali ke dashboard untuk membuat klip pertama kamu.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <div
                key={job.id}
                onClick={() => navigate(`/results/${job.id}`)}
                className="glass-card p-4 hover:border-brand-500/40 transition-all cursor-pointer flex items-center justify-between gap-4"
              >
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-white truncate text-base">
                    {job.video_title || 'Video Tanpa Judul'}
                  </h3>
                  <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {job.created_at ? new Date(job.created_at).toLocaleString('id-ID') : '-'}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium uppercase ${
                      job.status === 'completed' ? 'bg-success/10 text-success border border-success/20' :
                      job.status === 'failed' ? 'bg-danger/10 text-danger border border-danger/20' :
                      'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-white/30 shrink-0" />
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}