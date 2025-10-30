import type { PageLoad } from './$types';
import type { NetworkingData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/networking');
		const data: NetworkingData = await response.json();

		return {
			networking: data.networking || [],
			lastUpdated: data.lastUpdated
		};
	} catch (error) {
		console.error('Error loading networking:', error);
		return {
			networking: [],
			lastUpdated: null
		};
	}
};
