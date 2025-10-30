import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const skills = await getAllDocuments('skills');

		return json({
			skills: skills,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading skills:', error);
		return json({ error: 'Failed to load skills', skills: [] }, { status: 500 });
	}
};
