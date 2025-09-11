export const getRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMinutes < 1) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  return date.toLocaleDateString();
};

export interface TimestampInfo {
  timestamp: Date | null;
  color: string;
  allSame: boolean;
}

export const getGlobalTimestamp = (imageTimestamps: Map<string, Date>): TimestampInfo => {
  const timestamps = Array.from(imageTimestamps.values());
  if (timestamps.length === 0) return { timestamp: null, color: '#6c757d', allSame: false };

  // Find most recent timestamp
  const mostRecent = new Date(Math.max(...timestamps.map(t => t.getTime())));
  
  // Check if all timestamps are within 10 minutes of each other (same collection run)
  const oldestInCollection = new Date(Math.min(...timestamps.map(t => t.getTime())));
  const diffMinutes = (mostRecent.getTime() - oldestInCollection.getTime()) / (1000 * 60);
  const allSame = diffMinutes <= 10;

  // Determine color based on age
  const ageMinutes = (new Date().getTime() - mostRecent.getTime()) / (1000 * 60);
  let color = '#28a745'; // Green - fresh (< 30 min)
  if (ageMinutes > 120) color = '#dc3545'; // Red - old (> 2 hours)
  else if (ageMinutes > 60) color = '#ffc107'; // Yellow - moderate (> 1 hour)

  return { timestamp: mostRecent, color, allSame };
};