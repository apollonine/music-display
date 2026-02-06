import { motion } from 'framer-motion';
import { Music2, Radio, Disc3, Headphones } from 'lucide-react';

interface Props {
  isConnected: boolean;
  isAuthenticated: boolean;
  onAuth: () => void;
  activeSource?: string;
}

export function IdleScreen({ isConnected, isAuthenticated, onAuth, activeSource }: Props) {
  const getSourceIcon = () => {
    switch (activeSource) {
      case 'lastfm': return <Radio className="w-16 h-16 text-white/50" />;
      case 'audio': return <Disc3 className="w-16 h-16 text-white/50" />;
      case 'spotify': return <Headphones className="w-16 h-16 text-white/50" />;
      default: return <Music2 className="w-16 h-16 text-white/50" />;
    }
  };

  const getSourceLabel = () => {
    switch (activeSource) {
      case 'lastfm': return 'Last.fm';
      case 'audio': return 'Listening...';
      case 'spotify': return 'Spotify';
      case 'demo': return 'Demo Mode';
      default: return 'Music Display';
    }
  };

  return (
    <motion.div
      className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-zinc-900 to-black"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Animated background circles */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full bg-gradient-to-br from-purple-500/10 to-blue-500/10"
            style={{
              width: 300 + i * 100,
              height: 300 + i * 100,
              left: `${20 + i * 20}%`,
              top: `${30 + i * 10}%`,
            }}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 4 + i,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10 text-center">
        <motion.div
          className="mb-8"
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        >
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-zinc-800 to-zinc-900 flex items-center justify-center shadow-2xl">
            {getSourceIcon()}
          </div>
        </motion.div>

        <h1 className="text-3xl font-light text-white mb-2">{getSourceLabel()}</h1>
        
        {!isConnected ? (
          <motion.p
            className="text-white/50"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            Connecting to server...
          </motion.p>
        ) : !isAuthenticated ? (
          <div className="mt-6">
            <p className="text-white/50 mb-4">Connect your Spotify account to get started</p>
            <motion.button
              onClick={onAuth}
              className="px-8 py-3 bg-green-500 hover:bg-green-400 text-white font-medium rounded-full transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Connect Spotify
            </motion.button>
          </div>
        ) : (
          <motion.p
            className="text-white/50"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            Waiting for music...
          </motion.p>
        )}
      </div>

      {/* Status indicator */}
      <div className="absolute bottom-8 flex items-center gap-2 text-white/30 text-sm">
        <span
          className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
        />
        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>
    </motion.div>
  );
}
