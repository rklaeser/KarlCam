import type { PageLoad } from './$types';
import type { SkillsData } from '$lib/types';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params, fetch }) => {
	const response = await fetch('/api/skills');
	const data: SkillsData = await response.json();

	const skill = data.skills.find(s => s.id === params.id);

	if (!skill) {
		throw error(404, 'Skill not found');
	}

	return {
		skill
	};
};
