import React from 'react';
import { Marker } from 'react-leaflet';
import { createMarkerIcon } from '../../utils/mapUtils';
import { Webcam, CameraConditions } from '../../types';

interface CameraMarkerProps {
  webcam: Webcam;
  cameraData?: CameraConditions | undefined;
  imageUrl?: string | undefined;
  isLoading: boolean;
  onMarkerClick: (webcam: Webcam) => void;
}

const CameraMarker: React.FC<CameraMarkerProps> = ({
  webcam,
  cameraData,
  imageUrl,
  isLoading,
  onMarkerClick
}) => {
  const hasData = !!cameraData;
  const fogScore = cameraData?.fog_score ?? 0;
  
  const icon = createMarkerIcon(webcam.id, fogScore, hasData, imageUrl, isLoading);
  
  return (
    <Marker 
      key={webcam.id}
      position={[webcam.lat, webcam.lon]}
      icon={icon}
      eventHandlers={{
        click: () => onMarkerClick(webcam)
      }}
    />
  );
};

export default CameraMarker;