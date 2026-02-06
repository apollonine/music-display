import { motion } from 'framer-motion';
import type { TrackInfo } from '../types';
import { useColorExtraction } from '../hooks/useColorExtraction';

interface Props {
  track: TrackInfo;
}

export function MinimalDisplay({ track }: Props) {
  const colors = useColorExtraction(track.album_art_url);

  const progressPercent = track.duration_ms > 0
    ? (track.progress_ms / track.duration_ms) * 100
    : 0;

  return (
    <motion.div
      className="relative w-full h-full flex items-center justify-center overflow-hidden bg-black"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Subtle gradient accent */}
      <div
        className="absolute bottom-0 left-0 right-0 h-1"
        style={{
          background: `linear-gradient(90deg, ${colors.vibrant} 0%, ${colors.muted} 100%)`,
        }}
      />

      {/* Content */}
      <div className="flex items-center gap-8">
        {/* Album art */}
        <motion.img
          src={track.album_art_url || '/placeholder-album.png'}
          alt={track.album}
          className="w-32 h-32 rounded-lg shadow-xl"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        />

        {/* Track info */}
        <div className="flex flex-col">
          <motion.h1
            className="text-4xl font-light text-white tracking-tight"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {track.title}
          </motion.h1>
          <motion.p
            className="text-xl text-white/50 mt-1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {track.artist}
          </motion.p>

          {/* Minimal progress indicator */}
          <div className="mt-4 w-64">
            <div className="h-0.5 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: colors.vibrant }}
                animate={{ width: `${progressPercent}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Clock */}
      <div className="absolute top-6 right-8 text-white/30 text-sm font-mono">
        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </motion.div>
  );
}
