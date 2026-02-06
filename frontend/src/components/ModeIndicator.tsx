import { motion } from 'framer-motion';
import { Disc3, Mic2, User, Activity, Minimize2 } from 'lucide-react';
import type { DisplayMode } from '../types';

interface Props {
  currentMode: DisplayMode;
  onModeChange: (mode: DisplayMode) => void;
}

const modes: { mode: DisplayMode; icon: typeof Disc3; label: string }[] = [
  { mode: 'album_art', icon: Disc3, label: 'Album' },
  { mode: 'lyrics', icon: Mic2, label: 'Lyrics' },
  { mode: 'artist_info', icon: User, label: 'Artist' },
  { mode: 'visualizer', icon: Activity, label: 'Visualizer' },
  { mode: 'minimal', icon: Minimize2, label: 'Minimal' },
];

export function ModeIndicator({ currentMode, onModeChange }: Props) {
  return (
    <motion.div
      className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50"
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.5 }}
    >
      <div className="flex items-center gap-1 p-2 rounded-full bg-black/40 backdrop-blur-lg border border-white/10">
        {modes.map(({ mode, icon: Icon, label }) => (
          <motion.button
            key={mode}
            onClick={() => onModeChange(mode)}
            className={`relative p-3 rounded-full transition-colors ${
              currentMode === mode
                ? 'text-white'
                : 'text-white/40 hover:text-white/70'
            }`}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            title={label}
          >
            {currentMode === mode && (
              <motion.div
                className="absolute inset-0 rounded-full bg-white/20"
                layoutId="modeIndicator"
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
            <Icon className="relative w-5 h-5" />
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
