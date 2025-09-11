import L from 'leaflet';

export const getFogColor = (fogScore: number, hasData: boolean = true): string => {
  if (!hasData) return '#6c757d'; // Grey - No data
  if (fogScore < 20) return '#28a745'; // Green - Clear
  if (fogScore < 40) return '#ffc107'; // Yellow - Light fog
  if (fogScore < 60) return '#fd7e14'; // Orange - Moderate fog
  if (fogScore < 80) return '#dc3545'; // Red - Heavy fog
  return '#6f42c1'; // Purple - Very heavy fog
};

export const createMarkerIcon = (
  _webcamId: string, 
  fogScore: number, 
  hasData: boolean = true,
  imageUrl?: string,
  isLoading: boolean = false
): L.DivIcon => {
  const borderColor = getFogColor(fogScore, hasData);
  const size = 80;
  
  // Build the inner content based on state
  let innerContent: string;
  if (imageUrl) {
    innerContent = `<img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" alt="Camera view" />`;
  } else if (isLoading) {
    innerContent = '<div style="animation: pulse 2s infinite;">📷</div>';
  } else {
    innerContent = '📷';
  }
  
  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      border: 3px solid ${borderColor};
      border-radius: 50%;
      overflow: hidden;
      position: relative;
      background: white;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #666;
      font-size: 16px;
    ">
      ${innerContent}
    </div>
    <style>
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
    </style>
  `;

  return L.divIcon({
    html: html,
    className: 'camera-marker',
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -(size/2) - 5]
  });
};

export const getFogBadgeColor = (level: string): string => {
  switch (level.toLowerCase()) {
    case 'clear': return 'bg-green-100 text-green-800';
    case 'light fog': return 'bg-yellow-100 text-yellow-800';
    case 'moderate fog': return 'bg-orange-100 text-orange-800';
    case 'heavy fog': return 'bg-red-100 text-red-800';
    case 'very heavy fog': return 'bg-purple-100 text-purple-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};