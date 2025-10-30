import type { PageLoad } from './$types';
import type { ProjectsData } from '$lib/types';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params, fetch }) => {
	const response = await fetch('/api/projects');
	const data: ProjectsData = await response.json();

	const project = data.projects.find(p => p.id === params.id);

	if (!project) {
		throw error(404, 'Project not found');
	}

	return {
		project
	};
};
