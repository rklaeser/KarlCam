import { useEffect, useState } from 'react';

interface Webcam {
  id: string;
  name: string;
  lat: number;
  lon: number;
  url: string;
  video_url?: string;
  description: string;
  active: boolean;
}

export const useCameraImages = (webcams: Webcam[], apiBase: string) => {
  const [markerImages, setMarkerImages] = useState<Map<string, string>>(new Map());
  const [loadingImages, setLoadingImages] = useState<Set<string>>(new Set());
  const [imageTimestamps, setImageTimestamps] = useState<Map<string, Date>>(new Map());

  useEffect(() => {
    if (webcams.length === 0) return;

    console.log('🚀 Loading images for', webcams.length, 'webcams');
    
    const abortController = new AbortController();
    
    const loadImage = async (webcam: Webcam) => {
      try {
        const response = await fetch(
          `${apiBase}/api/public/cameras/${webcam.id}/latest-image`,
          { signal: abortController.signal }
        );
        const data = await response.json();
        
        if (response.ok && data.image_url) {
          console.log(`✅ Loaded image for ${webcam.id}`, data);
          
          // Update state immediately for this specific image
          setMarkerImages(prev => new Map(prev.set(webcam.id, data.image_url)));
          
          // Store timestamp if available
          if (data.timestamp) {
            const timestamp = new Date(data.timestamp);
            setImageTimestamps(prev => new Map(prev.set(webcam.id, timestamp)));
          }
          
          setLoadingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(webcam.id);
            return newSet;
          });
        } else {
          console.warn(`⚠️ No image for ${webcam.id}`);
          setLoadingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(webcam.id);
            return newSet;
          });
        }
      } catch (error: unknown) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error(`❌ Failed to load image for ${webcam.id}:`, error);
        }
        setLoadingImages(prev => {
          const newSet = new Set(prev);
          newSet.delete(webcam.id);
          return newSet;
        });
      }
    };
    
    // Clear previous images and set loading state
    setMarkerImages(new Map());
    setImageTimestamps(new Map());
    setLoadingImages(new Set(webcams.map(w => w.id)));
    
    // Start loading all images independently
    webcams.forEach(webcam => loadImage(webcam));
    
    // Cleanup function
    return () => {
      abortController.abort();
    };
  }, [webcams, apiBase]);

  const fetchImage = async (webcamId: string): Promise<string | null> => {
    try {
      const response = await fetch(`${apiBase}/api/public/cameras/${webcamId}/latest-image`);
      const data = await response.json();
      
      if (response.ok && data.image_url) {
        // Cache it for future use
        setMarkerImages(prev => new Map(prev.set(webcamId, data.image_url)));
        
        // Store timestamp if available
        if (data.timestamp) {
          const timestamp = new Date(data.timestamp);
          setImageTimestamps(prev => new Map(prev.set(webcamId, timestamp)));
        }
        
        return data.image_url;
      }
      return null;
    } catch (error) {
      console.error(`Failed to fetch image for ${webcamId}:`, error);
      return null;
    }
  };

  return {
    markerImages,
    loadingImages,
    imageTimestamps,
    fetchImage
  };
};