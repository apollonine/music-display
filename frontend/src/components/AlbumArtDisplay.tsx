import { motion } from 'framer-motion';
import type { TrackInfo } from '../types';
import { useColorExtraction } from '../hooks/useColorExtraction';

interface Props {
  track: TrackInfo;
}

export function AlbumArtDisplay({ track }: Props) {
  const colors = useColorExtraction(track.album_art_url);

  const progressPercent = track.duration_ms > 0 
    ? (track.progress_ms / track.duration_ms) * 100 
    : 0;

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      className="relative w-full h-full flex items-center justify-center overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Animated gradient background */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            `radial-gradient(ellipse at 30% 20%, ${colors.vibrant}40 0%, transparent 50%),
             radial-gradient(ellipse at 70% 80%, ${colors.muted}40 0%, transparent 50%),
             linear-gradient(180deg, ${colors.darkMuted} 0%, #000 100%)`,
            `radial-gradient(ellipse at 70% 30%, ${colors.muted}40 0%, transparent 50%),
             radial-gradient(ellipse at 30% 70%, ${colors.vibrant}40 0%, transparent 50%),
             linear-gradient(180deg, ${colors.darkMuted} 0%, #000 100%)`,
          ],
        }}
        transition={{ duration: 10, repeat: Infinity, repeatType: 'reverse' }}
      />

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center px-8 max-w-2xl">
        {/* Album art with shadow and glow */}
        <motion.div
          className="relative mb-8"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        >
          {/* Glow effect */}
          <div
            className="absolute inset-0 blur-3xl opacity-60 scale-110"
            style={{ backgroundColor: colors.vibrant }}
          />
          
          {/* Album art */}
          <motion.img
            key={track.album_art_url}
            src={track.album_art_url || '/placeholder-album.png'}
            alt={track.album}
            className="relative w-72 h-72 md:w-96 md:h-96 rounded-lg shadow-2xl object-cover"
            initial={{ opacity: 0, rotateY: -10 }}
            animate={{ opacity: 1, rotateY: 0 }}
            transition={{ duration: 0.6 }}
            style={{
              boxShadow: `0 25px 50px -12px ${colors.darkVibrant}80`,
            }}
          />

          {/* Vinyl record effect (visible when playing) */}
          {track.is_playing && (
            <motion.div
              className="absolute -right-16 top-1/2 -translate-y-1/2 w-72 h-72 md:w-96 md:h-96 rounded-full bg-gradient-to-br from-zinc-800 to-zinc-900"
              initial={{ x: -100, opacity: 0 }}
              animate={{ x: 0, opacity: 0.8, rotate: 360 }}
              transition={{
                x: { duration: 0.5 },
                opacity: { duration: 0.5 },
                rotate: { duration: 3, repeat: Infinity, ease: 'linear' },
              }}
              style={{ zIndex: -1 }}
            >
              <div className="absolute inset-8 rounded-full bg-gradient-to-br from-zinc-700 to-zinc-800" />
              <div className="absolute inset-1/3 rounded-full bg-zinc-900" />
              <div className="absolute inset-[45%] rounded-full" style={{ backgroundColor: colors.dominant }} />
            </motion.div>
          )}
        </motion.div>

        {/* Track info */}
        <motion.div
          className="text-center"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2 line-clamp-2">
            {track.title}
          </h1>
          <p className="text-xl md:text-2xl text-white/70 mb-1">
            {track.artist}
          </p>
          <p className="text-lg text-white/50">
            {track.album}
            {track.release_year && ` • ${track.release_year}`}
          </p>
        </motion.div>

        {/* Progress bar */}
        <div className="w-full mt-8">
          <div className="relative h-1 bg-white/20 rounded-full overflow-hidden">
            <motion.div
              className="absolute left-0 top-0 h-full rounded-full"
              style={{ backgroundColor: colors.vibrant }}
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <div className="flex justify-between mt-2 text-sm text-white/50">
            <span>{formatTime(track.progress_ms)}</span>
            <span>{formatTime(track.duration_ms)}</span>
          </div>
        </div>

        {/* Source indicator */}
        <div className="mt-4 flex items-center gap-2 text-white/40 text-sm">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span className="capitalize">{track.source}</span>
        </div>
      </div>
    </motion.div>
  );
}
