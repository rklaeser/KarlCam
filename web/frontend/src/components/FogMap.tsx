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
  const { markerImages, loadingImages, imageTimestamps, fetchImage } = useCameraImages(webcams, apiBase);
  
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
            // Find corresponding camera conditions
            const cameraData = cameras.find(cam => 
              cam.id === webcam.id || 
              (Math.abs(cam.lat - webcam.lat) < 0.001 && Math.abs(cam.lon - webcam.lon) < 0.001)
            );
            
            return (
              <CameraMarker
                key={webcam.id}
                webcam={webcam}
                cameraData={cameraData || undefined}
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