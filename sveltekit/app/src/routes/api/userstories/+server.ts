import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const userstories = await getAllDocuments('userstories');

		return json({
			userstories: userstories,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading user stories:', error);
		return json({ error: 'Failed to load user stories', userstories: [] }, { status: 500 });
	}
};
