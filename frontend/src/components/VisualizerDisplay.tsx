import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import type { TrackInfo } from '../types';
import { useColorExtraction } from '../hooks/useColorExtraction';

interface Props {
  track: TrackInfo;
}

export function VisualizerDisplay({ track }: Props) {
  const colors = useColorExtraction(track.album_art_url);
  const [bars, setBars] = useState<number[]>(Array(32).fill(0.3));

  useEffect(() => {
    if (!track.is_playing) return;

    const interval = setInterval(() => {
      setBars(prev => prev.map(() => 0.2 + Math.random() * 0.8));
    }, 100);

    return () => clearInterval(interval);
  }, [track.is_playing]);

  return (
    <motion.div
      className="relative w-full h-full flex flex-col items-center justify-center overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Background */}
      <div
        className="absolute inset-0"
        style={{
          background: `radial-gradient(ellipse at center, ${colors.darkMuted} 0%, #000 100%)`,
        }}
      />

      {/* Visualizer bars */}
      <div className="relative z-10 flex items-end justify-center gap-1 h-64 mb-12">
        {bars.map((height, index) => (
          <motion.div
            key={index}
            className="w-3 rounded-t-full"
            style={{
              background: `linear-gradient(180deg, ${colors.vibrant} 0%, ${colors.muted} 100%)`,
            }}
            animate={{
              height: track.is_playing ? `${height * 100}%` : '20%',
              opacity: track.is_playing ? 0.8 + height * 0.2 : 0.3,
            }}
            transition={{ duration: 0.1, ease: 'easeOut' }}
          />
        ))}
      </div>

      {/* Album art (small) */}
      <motion.img
        src={track.album_art_url || '/placeholder-album.png'}
        alt={track.album}
        className="relative z-10 w-24 h-24 rounded-lg shadow-2xl mb-4"
        animate={{
          scale: track.is_playing ? [1, 1.05, 1] : 1,
        }}
        transition={{
          duration: 0.5,
          repeat: track.is_playing ? Infinity : 0,
          repeatDelay: 0.5,
        }}
      />

      {/* Track info */}
      <div className="relative z-10 text-center">
        <h2 className="text-2xl font-bold text-white">{track.title}</h2>
        <p className="text-white/60">{track.artist}</p>
      </div>

      {/* Playing indicator */}
      {track.is_playing && (
        <motion.div
          className="absolute bottom-8 flex items-center gap-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-1 bg-white rounded-full"
                animate={{ height: ['8px', '16px', '8px'] }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.2,
                }}
              />
            ))}
          </div>
          <span className="text-white/50 text-sm ml-2">Playing</span>
        </motion.div>
      )}
    </motion.div>
  );
}
