import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, RefreshCw, CheckCircle2, XCircle, Ban, Loader2 } from 'lucide-react'
import useJobStatus from '../hooks/useJobStatus'
import ProgressTracker from '../components/ProgressTracker'
import ClipCard from '../components/ClipCard'

export default function Results() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const { job, isConnected, error } = useJobStatus(jobId)

  // 1. Penanganan saat data awal belum tersedia
  if (!job && !error) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-4">
        <Loader2 className="w-10 h-10 animate-spin text-brand-400 mb-4" />
        <p className="text-white/60 text-sm">Memuat data job...</p>
      </main>
    )
  }

  // 2. Penanganan jika request gagal total
  if (error && !job) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-4">
        <XCircle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-white font-bold text-lg mb-1">Gagal Memuat Job</h2>
        <p className="text-white/50 text-sm mb-6">{error}</p>
        <button 
          type="button"
          onClick={() => navigate('/')} 
          className="btn-secondary py-2 px-4 text-sm flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Kembali ke Dashboard
        </button>
      </main>
    )
  }

  const isCompleted = job?.status === 'completed'
  const isFailed    = job?.status === 'failed'
  const isCancelled = job?.status === 'cancelled'

  // Normalisasi data clips agar selalu berupa Array yang valid
  let rawClips = job?.clips || []
  if (typeof rawClips === 'string') {
    try {
      rawClips = JSON.parse(rawClips)
    } catch {
      rawClips = []
    }
  }
  const clips = Array.isArray(rawClips) ? rawClips : []

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="max-w-6xl mx-auto">

        {/* ── Header ──────────────────────────────────────── */}
        <div className="flex items-center gap-4 mb-8">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-secondary py-2 px-4 text-sm flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Kembali
          </button>
          
          {job?.video_title && (
            <div className="flex-1 min-w-0">
              <h1 className="font-display text-lg font-bold text-white truncate">
                {job.video_title}
              </h1>
              <p className="text-xs text-white/40 font-mono truncate mt-0.5">
                Job: {jobId}
              </p>
            </div>
          )}

          {/* Status Koneksi */}
          <div className={`flex items-center gap-1.5 text-xs ${isConnected ? 'text-success' : 'text-white/30'}`}>
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success animate-pulse' : 'bg-white/20'}`} />
            {isConnected ? 'Live' : 'Offline'}
          </div>
        </div>

        {/* ── Progress Tracker ─────────────────────────────── */}
        <AnimatePresence mode="wait">
          {!isCompleted && !isFailed && !isCancelled && (
            <motion.div
              key="progress"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-10"
            >
              <ProgressTracker job={job} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Banner Status Selesai ────────────────────────── */}
        {isCompleted && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-6 mb-8 border border-success/20 bg-success/5 flex items-center gap-4"
          >
            <CheckCircle2 className="w-8 h-8 text-success shrink-0" />
            <div>
              <h2 className="font-display font-bold text-white text-lg">
                🎉 {clips.length} Klip Viral Berhasil Dibuat!
              </h2>
              <p className="text-white/50 text-sm mt-0.5">
                {job?.status_message || 'Semua klip video selesai diproses.'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="ml-auto btn-secondary py-2 px-4 text-sm"
            >
              Buat Lagi
            </button>
          </motion.div>
        )}

        {/* ── Banner Status Gagal ──────────────────────────── */}
        {isFailed && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-6 mb-8 border border-danger/20 bg-danger/5"
          >
            <div className="flex items-center gap-4">
              <XCircle className="w-8 h-8 text-danger shrink-0" />
              <div>
                <h2 className="font-display font-bold text-white text-lg">Processing Gagal</h2>
                <p className="text-white/50 text-sm mt-0.5">
                  {job?.error_message || 'Terjadi kesalahan pada server saat memproses video.'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/')}
                className="ml-auto btn-secondary py-2 px-4 text-sm flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Coba Lagi
              </button>
            </div>
          </motion.div>
        )}

        {/* ── Banner Status Batal ──────────────────────────── */}
        {isCancelled && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-6 mb-8 border border-red-500/20 bg-red-500/5"
          >
            <div className="flex items-center gap-4">
              <Ban className="w-8 h-8 text-red-400 shrink-0" />
              <div>
                <h2 className="font-display font-bold text-white text-lg">Proses Dibatalkan</h2>
                <p className="text-white/50 text-sm mt-0.5">
                  {job?.status_message || 'Pemrosesan video ini telah dibatalkan.'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/')}
                className="ml-auto btn-secondary py-2 px-4 text-sm"
              >
                Buat Job Baru
              </button>
            </div>
          </motion.div>
        )}

        {/* ── Thumbnail Video (Saat Sedang Berjalan) ───────── */}
        {job?.thumbnail_url && !isCompleted && !isFailed && !isCancelled && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-center mb-8"
          >
            <div className="relative max-w-sm w-full rounded-2xl overflow-hidden border border-white/10">
              <img
                src={job.thumbnail_url}
                alt="Video thumbnail"
                className="w-full object-cover opacity-70"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-black/50 backdrop-blur flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
                </div>
              </div>
              <div className="absolute bottom-0 inset-x-0 p-4 bg-gradient-to-t from-black/80">
                <p className="text-white font-medium text-sm truncate">{job.video_title}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Galeri Klip Video ────────────────────────────── */}
        {clips.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-display text-2xl font-bold text-white">
                🎬 Hasil Klip Viral
              </h2>
              <span className="badge badge-brand">
                {clips.length} klip
              </span>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {clips.map((clip, index) => (
                <motion.div
                  key={clip?.id || `clip-${index}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <ClipCard clip={clip} index={index + 1} />
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* ── State Menunggu Hasil Selesai ─────────────────── */}
        {clips.length === 0 && !isFailed && !isCancelled && !isCompleted && (
          <div className="text-center py-16 text-white/30">
            <Loader2 className="w-10 h-10 mx-auto mb-4 animate-spin text-brand-600" />
            <p className="text-lg">Klip sedang diproses...</p>
            <p className="text-sm mt-2">Hasilnya akan muncul di sini secara otomatis</p>
          </div>
        )}

      </div>
    </main>
  )
}