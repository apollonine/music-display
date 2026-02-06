import { useEffect, useState, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useWebSocket } from './hooks/useWebSocket';
import { AlbumArtDisplay } from './components/AlbumArtDisplay';
import { LyricsDisplay } from './components/LyricsDisplay';
import { ArtistInfoDisplay } from './components/ArtistInfoDisplay';
import { VisualizerDisplay } from './components/VisualizerDisplay';
import { MinimalDisplay } from './components/MinimalDisplay';
import { IdleScreen } from './components/IdleScreen';
import { ModeIndicator } from './components/ModeIndicator';
import type { DisplayMode } from './types';

function App() {
  const { isConnected, track, mode, sendMessage } = useWebSocket();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [activeSource, setActiveSource] = useState<string>('demo');
  const [currentMode, setCurrentMode] = useState<DisplayMode>(mode);

  useEffect(() => {
    setCurrentMode(mode);
  }, [mode]);

  useEffect(() => {
    // Check auth status on mount
    fetch('/api/auth/status')
      .then(res => res.json())
      .then(data => {
        setIsAuthenticated(data.spotify);
        setIsDemoMode(data.demo_mode);
        setActiveSource(data.active_source || 'demo');
      })
      .catch(() => setIsAuthenticated(false));

    // Check for auth success from callback
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'success') {
      setIsAuthenticated(true);
      window.history.replaceState({}, '', '/');
    }
  }, []);

  const handleAuth = useCallback(() => {
    window.location.href = '/api/auth/spotify';
  }, []);

  const handleModeChange = useCallback((newMode: DisplayMode) => {
    setCurrentMode(newMode);
    fetch(`/api/display/mode/${newMode}`, { method: 'POST' });
  }, []);

  // Keyboard controls for development/testing
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const modes: DisplayMode[] = ['album_art', 'lyrics', 'artist_info', 'visualizer', 'minimal'];
      const currentIndex = modes.indexOf(currentMode);

      if (e.key === 'ArrowRight') {
        const nextMode = modes[(currentIndex + 1) % modes.length];
        handleModeChange(nextMode);
      } else if (e.key === 'ArrowLeft') {
        const prevMode = modes[(currentIndex - 1 + modes.length) % modes.length];
        handleModeChange(prevMode);
      } else if (e.key === ' ') {
        e.preventDefault();
        fetch('/api/control/play-pause', { method: 'POST' });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentMode, handleModeChange]);

  const renderDisplay = () => {
    if (!track) {
      return (
        <IdleScreen
          isConnected={isConnected}
          isAuthenticated={isAuthenticated || isDemoMode}
          onAuth={handleAuth}
          activeSource={activeSource}
        />
      );
    }

    switch (currentMode) {
      case 'album_art':
        return <AlbumArtDisplay track={track} />;
      case 'lyrics':
        return <LyricsDisplay track={track} />;
      case 'artist_info':
        return <ArtistInfoDisplay track={track} />;
      case 'visualizer':
        return <VisualizerDisplay track={track} />;
      case 'minimal':
        return <MinimalDisplay track={track} />;
      default:
        return <AlbumArtDisplay track={track} />;
    }
  };

  return (
    <div className="w-full h-full bg-black">
      <AnimatePresence mode="wait">
        {renderDisplay()}
      </AnimatePresence>

      {track && (
        <ModeIndicator
          currentMode={currentMode}
          onModeChange={handleModeChange}
        />
      )}
    </div>
  );
}

export default App;
