// Utility functions for KarlCam

/**
 * Get fog marker color based on fog score
 */
export function getFogColor(fogScore: number | undefined): string {
	if (fogScore === undefined) return '#6c757d'; // gray
	if (fogScore < 20) return '#28a745'; // green
	if (fogScore < 40) return '#ffc107'; // yellow
	if (fogScore < 60) return '#fd7e14'; // orange
	if (fogScore < 80) return '#dc3545'; // red
	return '#6f42c1'; // purple
}

/**
 * Get fog badge color classes
 */
export function getFogBadgeColor(fogLevel: string | undefined): string {
	if (!fogLevel) return 'bg-gray-100 text-gray-700';

	const level = fogLevel.toLowerCase();
	if (level.includes('clear')) return 'bg-green-100 text-green-700';
	if (level.includes('light')) return 'bg-yellow-100 text-yellow-700';
	if (level.includes('moderate')) return 'bg-orange-100 text-orange-700';
	if (level.includes('heavy')) return 'bg-red-100 text-red-700';
	if (level.includes('very heavy')) return 'bg-purple-100 text-purple-700';

	return 'bg-gray-100 text-gray-700';
}

/**
 * San Francisco map center
 */
export const SF_CENTER: [number, number] = [37.7749, -122.4194];
