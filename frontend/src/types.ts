export type SourceType = 'spotify' | 'analog' | 'unknown';

export interface TrackInfo {
  id: string;
  title: string;
  artist: string;
  album: string;
  album_art_url?: string;
  album_art_colors?: string[];
  duration_ms: number;
  progress_ms: number;
  is_playing: boolean;
  source: SourceType;
  release_year?: number;
  genre?: string[];
  lyrics?: string;
  artist_image_url?: string;
  artist_bio?: string;
}

export type DisplayMode = 'album_art' | 'lyrics' | 'artist_info' | 'visualizer' | 'minimal';

export interface DisplayState {
  mode: DisplayMode;
  brightness: number;
  track?: TrackInfo;
}

export interface WSMessage {
  type: 'init' | 'track_update' | 'progress_update' | 'mode_change';
  track?: TrackInfo;
  state?: DisplayState;
  progress_ms?: number;
  is_playing?: boolean;
  mode?: DisplayMode;
}
