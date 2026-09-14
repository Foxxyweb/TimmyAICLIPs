import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ fullscreen = false }) {
  if (fullscreen) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-10 h-10 text-brand-400 animate-spin" />
        <p className="text-white/40 text-sm">Memuat...</p>
      </div>
    )
  }
  
  return <Loader2 className="w-5 h-5 text-brand-400 animate-spin" />
}
