import type { PageLoad } from './$types';
import type { ValuesData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/values');
		const data: ValuesData = await response.json();

		return {
			values: data.values || [],
			lastUpdated: data.lastUpdated
		};
	} catch (error) {
		console.error('Error loading values:', error);
		return {
			values: [],
			lastUpdated: null
		};
	}
};
