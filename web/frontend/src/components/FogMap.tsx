import React, { useState } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import { SF_CENTER, SF_BOUNDS } from '../utils/leaflet-config';
import { useCameraImages } from '../hooks/useCameraImages';
import { ErrorBoundaryWrapper } from './ErrorBoundary';
import CameraMarker from './Map/CameraMarker';
import FogLegend from './Map/FogLegend';
import TimestampIndicator from './Map/TimestampIndicator';
import CameraModal from './Map/CameraModal';
import { Webcam, CameraConditions } from '../types';

interface FogMapProps {
  webcams: Webcam[];
  cameras?: CameraConditions[];
  apiBase: string;
}

const FogMap: React.FC<FogMapProps> = ({ webcams, cameras = [], apiBase }) => {
  // Use custom hook for image management
  const { markerImages, loadingImages, imageTimestamps, cameraData, fetchImage } = useCameraImages(webcams, apiBase);
  
  // Modal state
  const [selectedWebcam, setSelectedWebcam] = useState<Webcam | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleMarkerClick = (webcam: Webcam) => {
    setSelectedWebcam(webcam);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedWebcam(null);
  };

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={SF_CENTER}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        bounds={SF_BOUNDS}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        
        {/* Render markers only when images are loaded */}
        {webcams
          .filter(webcam => markerImages.has(webcam.id))
          .map(webcam => {
            // Get camera data from on-demand hook (preferred) or fallback to batch data
            const latestData = cameraData.get(webcam.id);
            const batchData = cameras.find(cam =>
              cam.id === webcam.id ||
              (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
            );

            // Convert on-demand data to CameraConditions format if available
            const cameraConditions = latestData ? {
              id: latestData.camera_id,
              name: latestData.camera_name,
              lat: latestData.latitude,
              lon: latestData.longitude,
              description: latestData.description,
              fog_score: latestData.fog_score ?? 0,
              fog_level: latestData.fog_level,
              confidence: latestData.confidence,
              weather_detected: latestData.weather_conditions && latestData.weather_conditions.length > 0,
              weather_confidence: latestData.confidence,
              timestamp: latestData.timestamp,
              active: true
            } : batchData;

            return (
              <CameraMarker
                key={webcam.id}
                webcam={webcam}
                cameraData={cameraConditions || undefined}
                imageUrl={markerImages.get(webcam.id) || undefined}
                isLoading={loadingImages.has(webcam.id)}
                onMarkerClick={handleMarkerClick}
              />
            );
          })}
      </MapContainer>
      
      <ErrorBoundaryWrapper>
        <FogLegend />
      </ErrorBoundaryWrapper>
      
      <ErrorBoundaryWrapper>
        <TimestampIndicator imageTimestamps={imageTimestamps} />
      </ErrorBoundaryWrapper>
      
      <ErrorBoundaryWrapper>
        <CameraModal
          isOpen={isModalOpen}
          webcam={selectedWebcam}
          cameras={cameras}
          onClose={closeModal}
          fetchImage={fetchImage}
          cachedImageUrl={selectedWebcam ? markerImages.get(selectedWebcam.id) || undefined : undefined}
        />
      </ErrorBoundaryWrapper>
    </div>
  );
};

export default FogMap;