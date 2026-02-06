import { motion } from 'framer-motion';
import type { TrackInfo } from '../types';
import { useColorExtraction } from '../hooks/useColorExtraction';

interface Props {
  track: TrackInfo;
}

export function ArtistInfoDisplay({ track }: Props) {
  const colors = useColorExtraction(track.artist_image_url || track.album_art_url);

  return (
    <motion.div
      className="relative w-full h-full flex items-center justify-center overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Background */}
      <div className="absolute inset-0">
        {(track.artist_image_url || track.album_art_url) && (
          <img
            src={track.artist_image_url || track.album_art_url}
            alt=""
            className="w-full h-full object-cover blur-3xl opacity-40 scale-110"
          />
        )}
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${colors.darkMuted}dd 0%, #000000ee 100%)`,
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center gap-12 px-12 max-w-5xl">
        {/* Artist image */}
        <motion.div
          className="flex-shrink-0"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        >
          <div
            className="w-64 h-64 rounded-full overflow-hidden shadow-2xl"
            style={{
              boxShadow: `0 25px 50px -12px ${colors.darkVibrant}80`,
            }}
          >
            <img
              src={track.artist_image_url || track.album_art_url || '/placeholder-artist.png'}
              alt={track.artist}
              className="w-full h-full object-cover"
            />
          </div>
        </motion.div>

        {/* Artist info */}
        <motion.div
          className="flex-1"
          initial={{ x: 30, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <p className="text-white/50 text-lg uppercase tracking-wider mb-2">Artist</p>
          <h1 className="text-5xl font-bold text-white mb-6">{track.artist}</h1>

          {/* Genres */}
          {track.genre && track.genre.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {track.genre.map((genre, index) => (
                <motion.span
                  key={genre}
                  className="px-4 py-2 rounded-full text-sm font-medium"
                  style={{
                    backgroundColor: `${colors.vibrant}40`,
                    color: colors.lightVibrant,
                  }}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                >
                  {genre}
                </motion.span>
              ))}
            </div>
          )}

          {/* Currently playing */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 backdrop-blur-sm">
            <img
              src={track.album_art_url || '/placeholder-album.png'}
              alt={track.album}
              className="w-16 h-16 rounded-lg"
            />
            <div>
              <p className="text-white/50 text-sm">Now Playing</p>
              <p className="text-white font-medium">{track.title}</p>
              <p className="text-white/60 text-sm">{track.album}</p>
            </div>
          </div>

          {/* Artist bio if available */}
          {track.artist_bio && (
            <motion.p
              className="mt-6 text-white/70 leading-relaxed line-clamp-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              {track.artist_bio}
            </motion.p>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}
