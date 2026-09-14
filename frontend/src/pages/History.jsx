import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { History as HistoryIcon, Trash2, Play, CheckCircle, XCircle, Loader2, Clock } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'

const STATUS_CONFIG = {
  pending:      { label: 'Menunggu',    color: 'text-white/40',  bg: 'bg-white/5',       icon: <Clock className="w-3 h-3" /> },
  downloading:  { label: 'Downloading', color: 'text-blue-400',  bg: 'bg-blue-500/10',  icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  transcribing: { label: 'Transcribing', color: 'text-yellow-400', bg: 'bg-yellow-500/10', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  analyzing:    { label: 'AI Analyzing', color: 'text-brand-400', bg: 'bg-brand-500/10', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  rendering:    { label: 'Rendering',   color: 'text-accent-400', bg: 'bg-accent-500/10', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  completed:    { label: 'Selesai',     color: 'text-success',   bg: 'bg-success/10',    icon: <CheckCircle className="w-3 h-3" /> },
  failed:       { label: 'Gagal',       color: 'text-danger',    bg: 'bg-danger/10',     icon: <XCircle className="w-3 h-3" /> },
  cancelled:    { label: 'Dibatalkan',  color: 'text-red-400',   bg: 'bg-red-500/10',    icon: <XCircle className="w-3 h-3" /> },
}

export default function History() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchJobs = async () => {
    try {
      const res = await axios.get('/api/jobs')
      setJobs(res.data)
    } catch (err) {
      toast.error('Gagal memuat history')
    } finally {
      setIsLoading(false)
    }
  }

  const deleteJob = async (jobId, e) => {
    e.stopPropagation()
    if (!confirm('Hapus job ini?')) return
    try {
      await axios.delete(`/api/jobs/${jobId}`)
      setJobs(prev => prev.filter(j => j.id !== jobId))
      toast.success('Job dihapus!')
    } catch {
      toast.error('Gagal menghapus job')
    }
  }

  useEffect(() => { fetchJobs() }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
      </div>
    )
  }

  return (
    <main className="min-h-screen py-10 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <HistoryIcon className="w-6 h-6 text-brand-400" />
          <h1 className="font-display text-2xl font-bold text-white">History Processing</h1>
          <span className="badge badge-brand ml-auto">{jobs.length} jobs</span>
        </div>

        {jobs.length === 0 ? (
          <div className="text-center py-20 text-white/30">
            <HistoryIcon className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg">Belum ada video yang diproses</p>
            <button onClick={() => navigate('/')} className="btn-primary mt-6">
              Buat Clips Pertama
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.map((job, i) => {
              const statusConf = STATUS_CONFIG[job.status] || STATUS_CONFIG.pending
              return (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => navigate(`/results/${job.id}`)}
                  className="glass-card-hover p-5 cursor-pointer flex items-center gap-4"
                >
                  {/* Thumbnail */}
                  {job.thumbnail_url ? (
                    <img
                      src={job.thumbnail_url}
                      alt=""
                      className="w-20 h-12 object-cover rounded-lg shrink-0 opacity-80"
                    />
                  ) : (
                    <div className="w-20 h-12 rounded-lg bg-surface-600 shrink-0 flex items-center justify-center">
                      <Play className="w-5 h-5 text-white/20" />
                    </div>
                  )}

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white truncate text-sm">
                      {job.video_title || 'Video tanpa judul'}
                    </p>
                    <p className="text-xs text-white/30 mt-0.5 truncate font-mono">
                      {job.youtube_url}
                    </p>
                  </div>

                  {/* Status badge */}
                  <div className={`badge ${statusConf.bg} ${statusConf.color} gap-1.5 shrink-0`}>
                    {statusConf.icon}
                    {statusConf.label}
                  </div>

                  {/* Clips count */}
                  {job.clips?.length > 0 && (
                    <span className="text-xs text-white/40 shrink-0">
                      {job.clips.length} klip
                    </span>
                  )}

                  {/* Delete */}
                  <button
                    onClick={(e) => deleteJob(job.id, e)}
                    className="text-white/20 hover:text-danger transition-colors shrink-0 p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}