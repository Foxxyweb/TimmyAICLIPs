import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Scissors, Zap, Youtube, Sparkles, ChevronRight, Play, Clock, Star } from 'lucide-react'
import toast from 'react-hot-toast'
import axios from 'axios'

// ── Base URL Backend Ngrok ────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// ── Feature Cards Data ────────────────────────────────────────
const FEATURES = [
  {
    icon: <Youtube className="w-6 h-6" />,
    title: 'Auto Download',
    desc: 'Paste URL YouTube, yt-dlp handle semuanya. Support 1080p, 4K, dan playlist.',
    color: 'from-red-500/20 to-red-600/10',
    border: 'border-red-500/20',
  },
  {
    icon: <Zap className="w-6 h-6 text-yellow-400" />,
    title: 'Whisper Transcribe',
    desc: 'faster-whisper mengtranskripsi audio dengan word-level timestamp yang akurat.',
    color: 'from-yellow-500/20 to-amber-600/10',
    border: 'border-yellow-500/20',
  },
  {
    icon: <Sparkles className="w-6 h-6 text-brand-400" />,
    title: 'TimmyAI',
    desc: 'TimmyAI deteksi momen paling viral & engaging dari konten videomu.',
    color: 'from-brand-500/20 to-purple-600/10',
    border: 'border-brand-500/20',
  },
  {
    icon: <Scissors className="w-6 h-6 text-accent-400" />,
    title: 'Auto Clip 9:16',
    desc: 'FFmpeg memotong, center-crop ke vertikal 9:16, dan tambah animated subtitles.',
    color: 'from-accent-500/20 to-cyan-600/10',
    border: 'border-accent-500/20',
  },
]

const EXAMPLE_URLS = [
  'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  'https://youtu.be/xvFZjo5PgG0',
]

// ── Home Page ─────────────────────────────────────────────────
export default function Home() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [maxClips, setMaxClips] = useState(5)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    
    const trimmedUrl = url.trim()
    if (!trimmedUrl) {
      toast.error('Masukkan URL YouTube terlebih dahulu!')
      return
    }
    
    if (!trimmedUrl.includes('youtube.com') && !trimmedUrl.includes('youtu.be')) {
      toast.error('URL harus berupa link YouTube yang valid!')
      return
    }

    setIsLoading(true)
    
    try {
      const response = await axios.post(`${API_BASE}/api/process-video`, {
        youtube_url: trimmedUrl,
        max_clips: maxClips,
      }, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        }
      })
      
      const { job_id } = response.data
      
      toast.success('Pipeline dimulai! Tracking progress...', { duration: 3000 })
      navigate(`/results/${job_id}`)
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Gagal memulai processing. Coba lagi!'
      toast.error(errorMsg)
      setIsLoading(false)
    }
  }, [url, maxClips, navigate])

  return (
    <main className="relative min-h-screen overflow-hidden">
      
      {/* ── Background decorations ─────────────────────────── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-500/8 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-900/20 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-16 lg:py-24">
        
        {/* ── Hero Section ──────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="text-center mb-16"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-400 text-sm font-medium mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
            Powered by Gemini 2.5 Flash + Whisper AI
          </motion.div>

          {/* Heading */}
          <h1 className="font-display text-5xl lg:text-7xl font-black leading-tight mb-6">
            <span className="text-white">AI Video</span>
            <br />
            <span className="bg-gradient-to-r from-brand-400 via-brand-300 to-accent-400 bg-clip-text text-transparent text-glow">
              Clipper
            </span>
          </h1>

          <p className="text-xl text-white/50 max-w-2xl mx-auto leading-relaxed font-light">
            Ubah video YouTube panjang menjadi{' '}
            <span className="text-white/80 font-medium">klip viral format 9:16</span>{' '}
            secara otomatis menggunakan AI. Dari URL ke TikTok-ready clips dalam hitungan menit.
          </p>
        </motion.div>

        {/* ── URL Input Card ─────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="glass-card gradient-border-card p-8 mb-12 animate-glow-pulse"
        >
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* URL Input */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-white/60">
                <Youtube className="w-4 h-4 text-red-400" />
                YouTube Video URL
              </label>
              
              <div className="relative">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="url-input pr-36"
                  disabled={isLoading}
                  autoFocus
                />
                
                {/* Clear button */}
                {url && (
                  <button
                    type="button"
                    onClick={() => setUrl('')}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors text-sm"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Quick example URLs */}
              <div className="flex items-center gap-2 text-xs text-white/30">
                <span>Contoh:</span>
                {EXAMPLE_URLS.map((exUrl, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setUrl(exUrl)}
                    className="text-brand-400/70 hover:text-brand-400 transition-colors underline underline-offset-2 truncate max-w-[140px]"
                  >
                    {exUrl.slice(0, 30)}...
                  </button>
                ))}
              </div>
            </div>

            {/* Settings Row */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-surface-800/50 border border-white/5">
              <Star className="w-4 h-4 text-yellow-400 shrink-0" />
              <span className="text-sm text-white/50 shrink-0">Jumlah klip:</span>
              <div className="flex items-center gap-2 flex-wrap">
                {[3, 5, 7, 10].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setMaxClips(n)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                      maxClips === n
                        ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/50'
                        : 'bg-surface-600/50 text-white/40 hover:text-white/70 hover:bg-surface-500/50'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <div className="ml-auto flex items-center gap-1.5 text-xs text-white/30">
                <Clock className="w-3 h-3" />
                <span>~{Math.ceil(maxClips * 0.5)} menit</span>
              </div>
            </div>

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: isLoading ? 1 : 1.01 }}
              whileTap={{ scale: isLoading ? 1 : 0.99 }}
              className="btn-primary w-full justify-center py-4 text-base rounded-xl"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Memulai pipeline...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Generate Viral Clips</span>
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </motion.button>
          </form>
        </motion.div>

        {/* ── Feature Cards ──────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {FEATURES.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className={`glass-card-hover p-5 border ${feature.border}`}
              style={{
                background: `linear-gradient(135deg, ${feature.color.split(' ')[1].replace('from-', '')} 0%, transparent 100%)`
              }}
            >
              <div className="mb-3 p-2 w-fit rounded-lg bg-white/5">
                {feature.icon}
              </div>
              <h3 className="font-display font-bold text-white mb-1.5 text-sm">
                {feature.title}
              </h3>
              <p className="text-xs text-white/45 leading-relaxed">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* ── Stats Row ──────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-16 flex justify-center gap-12 text-center"
        >
          {[
            { value: '100%', label: 'Open Source' },
            { value: 'Free', label: 'Gratis Selamanya' },
            { value: '9:16', label: 'Format Vertikal' },
          ].map((stat, i) => (
            <div key={i}>
              <div className="font-display text-3xl font-black bg-gradient-to-r from-brand-400 to-accent-400 bg-clip-text text-transparent">
                {stat.value}
              </div>
              <div className="text-xs text-white/35 mt-1 font-medium">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </main>
  )
}