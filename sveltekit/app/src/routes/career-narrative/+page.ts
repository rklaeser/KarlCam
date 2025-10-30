import type { PageLoad } from './$types';
import type { CareerNarrativeData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/career-narrative');
		const data: CareerNarrativeData = await response.json();

		return data || {};
	} catch (error) {
		console.error('Error loading career narrative:', error);
		return {};
	}
};
