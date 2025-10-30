import type { PageLoad } from './$types';
import type { CompaniesData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/companies');
		const data: CompaniesData = await response.json();

		return {
			companies: data.companies || [],
			lastUpdated: data.lastUpdated
		};
	} catch (error) {
		console.error('Error loading companies:', error);
		return {
			companies: [],
			lastUpdated: null
		};
	}
};
