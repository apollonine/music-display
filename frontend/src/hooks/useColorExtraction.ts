import { useState, useEffect } from 'react';

interface ColorPalette {
  dominant: string;
  vibrant: string;
  muted: string;
  darkVibrant: string;
  darkMuted: string;
  lightVibrant: string;
}

const defaultPalette: ColorPalette = {
  dominant: '#1a1a2e',
  vibrant: '#4a4a6a',
  muted: '#2a2a3e',
  darkVibrant: '#0a0a1e',
  darkMuted: '#1a1a2e',
  lightVibrant: '#6a6a8a',
};

export function useColorExtraction(imageUrl: string | undefined): ColorPalette {
  const [palette, setPalette] = useState<ColorPalette>(defaultPalette);

  useEffect(() => {
    if (!imageUrl) {
      setPalette(defaultPalette);
      return;
    }

    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Sample at small size for performance
      const sampleSize = 50;
      canvas.width = sampleSize;
      canvas.height = sampleSize;
      
      ctx.drawImage(img, 0, 0, sampleSize, sampleSize);
      const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize);
      const pixels = imageData.data;

      // Simple color extraction - find dominant colors
      const colorCounts: Map<string, number> = new Map();
      
      for (let i = 0; i < pixels.length; i += 4) {
        const r = Math.round(pixels[i] / 32) * 32;
        const g = Math.round(pixels[i + 1] / 32) * 32;
        const b = Math.round(pixels[i + 2] / 32) * 32;
        const key = `${r},${g},${b}`;
        colorCounts.set(key, (colorCounts.get(key) || 0) + 1);
      }

      // Sort by frequency
      const sortedColors = [...colorCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
        .map(([color]) => {
          const [r, g, b] = color.split(',').map(Number);
          return `rgb(${r}, ${g}, ${b})`;
        });

      setPalette({
        dominant: sortedColors[0] || defaultPalette.dominant,
        vibrant: sortedColors[1] || defaultPalette.vibrant,
        muted: sortedColors[2] || defaultPalette.muted,
        darkVibrant: sortedColors[3] || defaultPalette.darkVibrant,
        darkMuted: sortedColors[4] || defaultPalette.darkMuted,
        lightVibrant: sortedColors[5] || defaultPalette.lightVibrant,
      });
    };

    img.src = imageUrl;
  }, [imageUrl]);

  return palette;
}
