import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Download, CheckCircle, Loader2, Zap, 
  Brain, Scissors, Clock, TrendingUp, XCircle 
} from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'

// ── Pipeline Steps Config ─────────────────────────────────────
const PIPELINE_STEPS = [
  {
    key: 'downloading',
    label: 'Download Video',
    sublabel: 'yt-dlp',
    icon: <Download className="w-4 h-4" />,
    range: [0, 25],
    color: 'blue',
  },
  {
    key: 'transcribing',
    label: 'Transkripsi Audio',
    sublabel: 'Whisper AI',
    icon: <Zap className="w-4 h-4" />,
    range: [25, 55],
    color: 'yellow',
  },
  {
    key: 'analyzing',
    label: 'Analisis Viral',
    sublabel: 'Gemini 2.5 Flash',
    icon: <Brain className="w-4 h-4" />,
    range: [55, 70],
    color: 'purple',
  },
  {
    key: 'rendering',
    label: 'Render Klip 9:16',
    sublabel: 'FFmpeg',
    icon: <Scissors className="w-4 h-4" />,
    range: [70, 100],
    color: 'cyan',
  },
]

const STATUS_ORDER = ['pending', 'downloading', 'transcribing', 'analyzing', 'rendering', 'completed']

function getStepStatus(stepKey, currentStatus, progress) {
  if (currentStatus === 'completed') return 'done'
  if (currentStatus === 'failed' || currentStatus === 'cancelled') return 'idle'
  
  const currentIdx = STATUS_ORDER.indexOf(currentStatus)
  const stepIdx    = STATUS_ORDER.indexOf(stepKey)
  
  if (stepIdx < currentIdx) return 'done'
  if (stepKey === currentStatus) return 'active'
  return 'idle'
}

const STEP_COLORS = {
  blue:   { text: 'text-blue-400',   bg: 'bg-blue-500/20',   border: 'border-blue-500/40',   ring: 'ring-blue-500/30' },
  yellow: { text: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/40', ring: 'ring-yellow-500/30' },
  purple: { text: 'text-brand-400',  bg: 'bg-brand-500/20',  border: 'border-brand-500/40',  ring: 'ring-brand-500/30' },
  cyan:   { text: 'text-accent-400', bg: 'bg-accent-500/20', border: 'border-accent-500/40', ring: 'ring-accent-500/30' },
}

// ── ProgressTracker Component ─────────────────────────────────
export default function ProgressTracker({ job, onCancelSuccess }) {
  const [isCancelling, setIsCancelling] = useState(false)
  
  const status   = job?.status?.toLowerCase() || 'pending'
  const progress = job?.progress || 0
  const message  = job?.status_message || 'Menunggu...'
  
  const isRunning = ['pending', 'downloading', 'transcribing', 'analyzing', 'rendering'].includes(status)
  const isCancelled = status === 'cancelled'

  // Handler pemanggilan API Batal
  const handleCancel = async () => {
    if (!job?.id || isCancelling) return
    
    if (!confirm('Apakah kamu yakin ingin membatalkan proses download ini?')) return

    setIsCancelling(true)
    try {
      const res = await axios.post(`/api/jobs/${job.id}/cancel`)
      if (res.status === 200) {
        toast.success('Proses berhasil dibatalkan')
        if (onCancelSuccess) onCancelSuccess()
      }
    } catch (error) {
      console.error('Gagal membatalkan job:', error)
      toast.error('Gagal membatalkan proses')
    } finally {
      setIsCancelling(false)
    }
  }

  return (
    <div className="glass-card p-6 space-y-6">
      
      {/* Overall progress */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="font-display font-bold text-white text-lg flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-brand-400" />
            Progress Pipeline
          </h3>

          <div className="flex items-center gap-4">
            {isRunning && (
              <button
                onClick={handleCancel}
                disabled={isCancelling}
                className="flex items-center gap-1.5 text-xs font-semibold text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-50"
              >
                {isCancelling ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-red-400" />
                ) : (
                  <XCircle className="w-3.5 h-3.5" />
                )}
                {isCancelling ? 'Membatalkan...' : 'Batal'}
              </button>
            )}

            <span className={`font-mono font-bold text-lg ${isCancelled ? 'text-red-400' : 'text-brand-400'}`}>
              {isCancelled ? 'CANCELLED' : `${progress}%`}
            </span>
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="progress-bar">
          <motion.div
            className={`progress-bar-fill ${isCancelled ? 'bg-red-500' : ''}`}
            initial={{ width: 0 }}
            animate={{ width: isCancelled ? '100%' : `${progress}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>

        {/* Status message */}
        <motion.p
          key={message}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className={`text-sm flex items-center gap-2 ${isCancelled ? 'text-red-400' : 'text-white/50'}`}
        >
          {isRunning && <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400 shrink-0" />}
          {isCancelled && <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />}
          {message}
        </motion.p>
      </div>

      {/* Pipeline steps */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {PIPELINE_STEPS.map((step) => {
          const stepStatus = getStepStatus(step.key, status, progress)
          const colors = STEP_COLORS[step.color]
          
          return (
            <motion.div
              key={step.key}
              animate={{
                opacity: stepStatus === 'idle' ? 0.4 : 1,
              }}
              transition={{ duration: 0.3 }}
              className={`
                relative p-4 rounded-xl border transition-all duration-300
                ${stepStatus === 'done'   ? `${colors.bg} ${colors.border}` : ''}
                ${stepStatus === 'active' ? `${colors.bg} ${colors.border} ring-2 ${colors.ring}` : ''}
                ${stepStatus === 'idle'   ? 'bg-surface-700/30 border-white/5' : ''}
              `}
            >
              {/* Icon */}
              <div className={`
                w-8 h-8 rounded-lg flex items-center justify-center mb-3
                ${stepStatus === 'idle' ? 'bg-white/5 text-white/20' : `${colors.bg} ${colors.text}`}
              `}>
                {stepStatus === 'done' ? (
                  <CheckCircle className="w-4 h-4" />
                ) : stepStatus === 'active' ? (
                  <div className="animate-spin">{step.icon}</div>
                ) : (
                  step.icon
                )}
              </div>

              {/* Label */}
              <p className={`font-semibold text-xs ${stepStatus === 'idle' ? 'text-white/30' : 'text-white'}`}>
                {step.label}
              </p>
              <p className={`text-xs mt-0.5 font-mono ${stepStatus === 'idle' ? 'text-white/15' : colors.text}`}>
                {step.sublabel}
              </p>

              {/* Active pulse */}
              {stepStatus === 'active' && (
                <span className={`absolute top-2 right-2 w-2 h-2 rounded-full animate-pulse ${colors.text.replace('text', 'bg')}`} />
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Video info */}
      {job?.video_duration && (
        <div className="flex items-center gap-2 text-xs text-white/30 border-t border-white/5 pt-4">
          <Clock className="w-3 h-3" />
          <span>Durasi video: {Math.floor(job.video_duration / 60)}:{String(job.video_duration % 60).padStart(2, '0')}</span>
          <span className="ml-auto font-mono">Job: {job.id?.slice(0, 8)}...</span>
        </div>
      )}
    </div>
  )
}