import type { PageLoad } from './$types';
import type { ProjectsData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/projects');
		const data: ProjectsData = await response.json();

		return {
			projects: data.projects || [],
			lastUpdated: data.lastUpdated
		};
	} catch (error) {
		console.error('Error loading projects:', error);
		return {
			projects: [],
			lastUpdated: null
		};
	}
};
