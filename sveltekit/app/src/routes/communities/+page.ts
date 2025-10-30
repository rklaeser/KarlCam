import type { PageLoad } from './$types';
import type { CommunitiesData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/communities');
		const data: CommunitiesData = await response.json();

		return {
			communities: data.communities || [],
			lastUpdated: data.lastUpdated
		};
	} catch (error) {
		console.error('Error loading communities:', error);
		return {
			communities: [],
			lastUpdated: null
		};
	}
};
