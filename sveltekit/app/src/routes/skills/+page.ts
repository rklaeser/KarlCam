import type { PageLoad } from './$types';
import type { SkillsData } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/skills');
		const data: SkillsData = await response.json();

		return {
			skills: data.skills || [],
			lastUpdated: data.lastUpdated
		};
	} catch (error) {
		console.error('Error loading skills:', error);
		return {
			skills: [],
			lastUpdated: null
		};
	}
};
