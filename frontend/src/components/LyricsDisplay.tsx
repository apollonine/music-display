import { motion } from 'framer-motion';
import type { TrackInfo } from '../types';
import { useColorExtraction } from '../hooks/useColorExtraction';

interface Props {
  track: TrackInfo;
}

export function LyricsDisplay({ track }: Props) {
  const colors = useColorExtraction(track.album_art_url);

  const lyricsLines = track.lyrics?.split('\n') || [];

  return (
    <motion.div
      className="relative w-full h-full flex overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Background with album art blur */}
      <div className="absolute inset-0">
        {track.album_art_url && (
          <img
            src={track.album_art_url}
            alt=""
            className="w-full h-full object-cover blur-3xl opacity-30 scale-110"
          />
        )}
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(180deg, ${colors.darkMuted}ee 0%, #000000ee 100%)`,
          }}
        />
      </div>

      {/* Left side - Mini album art and track info */}
      <div className="relative z-10 w-1/3 p-8 flex flex-col justify-center items-center border-r border-white/10">
        <motion.img
          src={track.album_art_url || '/placeholder-album.png'}
          alt={track.album}
          className="w-40 h-40 rounded-lg shadow-2xl mb-6"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        />
        <h2 className="text-xl font-bold text-white text-center line-clamp-2">
          {track.title}
        </h2>
        <p className="text-white/60 text-center mt-1">{track.artist}</p>
      </div>

      {/* Right side - Lyrics */}
      <div className="relative z-10 flex-1 p-8 overflow-hidden">
        {track.lyrics ? (
          <motion.div
            className="h-full overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {lyricsLines.map((line, index) => (
              <motion.p
                key={index}
                className={`text-xl leading-relaxed mb-2 ${
                  line.trim() === '' ? 'h-4' : 'text-white/80'
                }`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + index * 0.02 }}
              >
                {line || '\u00A0'}
              </motion.p>
            ))}
          </motion.div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <motion.div
              className="text-center text-white/40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <p className="text-2xl mb-2">No lyrics available</p>
              <p className="text-lg">Lyrics couldn't be found for this track</p>
            </motion.div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
