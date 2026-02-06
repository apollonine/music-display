import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSMessage, TrackInfo, DisplayMode } from '../types';

interface UseWebSocketReturn {
  isConnected: boolean;
  track: TrackInfo | null;
  mode: DisplayMode;
  sendMessage: (message: object) => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [track, setTrack] = useState<TrackInfo | null>(null);
  const [mode, setMode] = useState<DisplayMode>('album_art');

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Reconnect after 2 seconds
      reconnectTimeout.current = setTimeout(connect, 2000);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.current.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        
        switch (message.type) {
          case 'init':
            if (message.track) setTrack(message.track);
            if (message.state?.mode) setMode(message.state.mode);
            break;
          
          case 'track_update':
            if (message.track) setTrack(message.track);
            break;
          
          case 'progress_update':
            setTrack(prev => prev ? {
              ...prev,
              progress_ms: message.progress_ms ?? prev.progress_ms,
              is_playing: message.is_playing ?? prev.is_playing,
            } : null);
            break;
          
          case 'mode_change':
            if (message.mode) setMode(message.mode);
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  return { isConnected, track, mode, sendMessage };
}
