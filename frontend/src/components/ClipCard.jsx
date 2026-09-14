import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Download, Play, Pause, TrendingUp, Clock, Zap, FileVideo, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function ViralScoreBadge({ score }) {
  const color = score >= 80 ? 'text-yellow-400 bg-yellow-500/15 border-yellow-500/30' :
                score >= 60 ? 'text-brand-400 bg-brand-500/15 border-brand-500/30' :
                              'text-white/50 bg-white/5 border-white/10'
  return (
    <div className={`badge ${color} gap-1`}>
      <Zap className="w-3 h-3" />
      {score}
    </div>
  )
}

export default function ClipCard({ clip, index }) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [blobVideoUrl, setBlobVideoUrl] = useState('')
  const [loadingVideo, setLoadingVideo] = useState(false)
  const videoRef = useRef(null)

  // 1. Susun URL Backend Video
  const rawUrl = clip.video_url || (clip.filename ? `/clips/${clip.filename}` : '')
  let initialUrl = rawUrl.startsWith('http') 
    ? rawUrl 
    : `${API_BASE}${rawUrl.startsWith('/') ? '' : '/'}${rawUrl}`

  // Sisipkan bypass header via Query Param untuk ngrok
  const separator = initialUrl.includes('?') ? '&' : '?'
  const directVideoUrl = initialUrl ? `${initialUrl}${separator}ngrok-skip-browser-warning=true` : ''

  // 2. Fetch video menjadi Blob agar terbebas 100% dari blokiran Ngrok & MIME Error
  useEffect(() => {
    let active = true
    if (!directVideoUrl) return

    const loadVideoBlob = async () => {
      try {
        setLoadingVideo(true)
        const res = await fetch(directVideoUrl, {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          }
        })
        if (!res.ok) throw new Error('Failed to load video stream')
        const blob = await res.blob()
        if (active) {
          const objectUrl = URL.createObjectURL(blob)
          setBlobVideoUrl(objectUrl)
        }
      } catch (err) {
        console.error("Gagal load blob video, fallback ke direct URL:", err)
        if (active) setBlobVideoUrl(directVideoUrl)
      } finally {
        if (active) setLoadingVideo(false)
      }
    }

    loadVideoBlob()

    return () => {
      active = false
      if (blobVideoUrl && blobVideoUrl.startsWith('blob:')) {
        URL.revokeObjectURL(blobVideoUrl)
      }
    }
  }, [directVideoUrl])

  const durationStr = clip.duration 
    ? `${Math.floor(clip.duration)}s`
    : `${Math.floor((clip.end_time || 0) - (clip.start_time || 0))}s`
  
  const fileSizeMB = clip.file_size 
    ? (clip.file_size / 1024 / 1024).toFixed(1)
    : null

  const handlePlayPause = () => {
    if (!videoRef.current) return
    
    if (isPlaying) {
      videoRef.current.pause()
    } else {
      videoRef.current.play().catch((err) => {
        console.error('Play error:', err)
      })
    }
  }

  const handleDownload = async () => {
    try {
      const targetUrl = blobVideoUrl || directVideoUrl
      const response = await fetch(targetUrl, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      })
      
      if (!response.ok) throw new Error('Gagal mengambil file video')

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = clip.filename || `clip_${index}.mp4`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      toast.success(`Klip ${index} berhasil diunduh!`)
    } catch (err) {
      console.error('Download error:', err)
      toast.error('Gagal mengunduh klip')
    }
  }

  return (
    <motion.div
      className="glass-card overflow-hidden group"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      {/* Video Preview (9:16) */}
      <div className="aspect-9-16 relative bg-surface-800 overflow-hidden flex items-center justify-center">
        {loadingVideo && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/40 z-10">
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin mb-2" />
            <span className="text-[11px] text-white/60">Memuat video...</span>
          </div>
        )}

        {blobVideoUrl ? (
          <>
            <video
              ref={videoRef}
              src={blobVideoUrl}
              className="w-full h-full object-cover"
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
              loop
              playsInline
              preload="auto"
            />
            
            {/* Tombol Play/Pause */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: isHovered || !isPlaying ? 1 : 0 }}
              className="absolute inset-0 flex items-center justify-center bg-black/30 z-20"
            >
              <button
                type="button"
                onClick={handlePlayPause}
                className="w-14 h-14 rounded-full bg-white/10 backdrop-blur border border-white/20 
                           flex items-center justify-center hover:bg-white/20 transition-colors pointer-events-auto cursor-pointer"
              >
                {isPlaying 
                  ? <Pause className="w-6 h-6 text-white fill-white" />
                  : <Play className="w-6 h-6 text-white fill-white ml-1" />
                }
              </button>
            </motion.div>
          </>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-white/20">
            <FileVideo className="w-10 h-10 mb-2" />
            <span className="text-xs">No preview</span>
          </div>
        )}

        {/* Badges */}
        <div className="absolute top-3 left-3 right-3 flex justify-between items-start pointer-events-none z-30">
          <div className="badge bg-black/60 text-white border-white/20">
            #{index}
          </div>
          <ViralScoreBadge score={clip.viral_score || 0} />
        </div>

        <div className="absolute bottom-3 right-3 pointer-events-none z-30">
          <div className="badge bg-black/70 text-white/80 border-white/10">
            <Clock className="w-3 h-3" />
            {durationStr}
          </div>
        </div>
      </div>

      {/* Info & Download */}
      <div className="p-4 space-y-3">
        <h3 className="font-display font-bold text-white text-sm leading-tight line-clamp-2">
          {clip.title || `Klip #${index}`}
        </h3>
        
        {clip.description && (
          <p className="text-xs text-white/40 leading-relaxed line-clamp-2">
            {clip.description}
          </p>
        )}

        <div className="flex items-center gap-3 text-xs text-white/30">
          <span className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            {clip.start_time?.toFixed(0)}s → {clip.end_time?.toFixed(0)}s
          </span>
          {fileSizeMB && (
            <span className="ml-auto">{fileSizeMB} MB</span>
          )}
        </div>

        <button
          type="button"
          onClick={handleDownload}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg 
                     bg-brand-600/20 hover:bg-brand-600/40 border border-brand-500/30 
                     text-brand-400 hover:text-white text-xs font-semibold
                     transition-all duration-200 group/btn cursor-pointer"
        >
          <Download className="w-3.5 h-3.5 group-hover/btn:animate-bounce-subtle" />
          Unduh Klip
        </button>
      </div>
    </motion.div>
  )
}