import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const projects = await getAllDocuments('projects');

		return json({
			projects: projects,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading projects:', error);
		return json({ error: 'Failed to load projects', projects: [] }, { status: 500 });
	}
};
